use anyhow::{Context, Result};
use indicatif::{ProgressBar, ProgressStyle};
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};

/// Downloads a file from `url` and saves it to `dest` with progress reporting.
pub async fn download_async(url: &str, dest: &Path) -> Result<bool> {
    let client = reqwest::Client::builder()
        .user_agent("neo-package-manager/0.1.0 (Gentoo Linux)")
        .build()
        .context("Failed to build HTTP client")?;

    let mut response = client.get(url).send().await.context("Failed to initiate download")?;
    if !response.status().is_success() {
        return Ok(false);
    }

    let total_size = response.content_length().unwrap_or(0);

    let pb = if total_size > 0 {
        let bar = ProgressBar::new(total_size);
        if let Ok(style) = ProgressStyle::default_bar()
            .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {bytes}/{total_bytes} ({eta})")
        {
            bar.set_style(style.progress_chars("#>-"));
        }
        Some(bar)
    } else {
        let bar = ProgressBar::new_spinner();
        bar.set_message("Downloading...");
        Some(bar)
    };

    if let Some(parent) = dest.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let temp_dest = dest.with_extension(format!("tmp.{}", std::process::id()));
    let mut file = File::create(&temp_dest)
        .context(format!("Failed to create temporary file at {:?}", temp_dest))?;

    while let Some(chunk) = response.chunk().await.context("Error reading response stream")? {
        file.write_all(&chunk)
            .context("Error writing chunk to file")?;
        if let Some(ref bar) = pb {
            bar.inc(chunk.len() as u64);
        }
    }

    file.flush().context("Error flushing download stream")?;
    drop(file);

    if let Some(bar) = pb {
        bar.finish_with_message("Download completed");
    }

    std::fs::rename(&temp_dest, dest)
        .context(format!("Failed to rename temporary file to destination {:?}", dest))?;

    Ok(true)
}

/// Synchronous wrapper around `download_async`
pub fn download_sync(url: &str, dest_str: &str) -> Result<bool> {
    let dest = PathBuf::from(dest_str);
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .context("Failed to create Tokio runtime")?;

    rt.block_on(download_async(url, &dest))
}

/// Downloads multiple files in parallel using Tokio tasks
pub fn download_parallel(tasks: &[(String, String)]) -> Result<Vec<bool>> {
    let rt = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(4)
        .enable_all()
        .build()
        .context("Failed to build multi-threaded Tokio runtime")?;

    rt.block_on(async {
        let mut handles = Vec::new();
        for (url, dest) in tasks {
            let u = url.clone();
            let d = PathBuf::from(dest);
            handles.push(tokio::spawn(async move {
                download_async(&u, &d).await.unwrap_or(false)
            }));
        }

        let mut results = Vec::new();
        for h in handles {
            results.push(h.await.unwrap_or(false));
        }
        Ok(results)
    })
}
