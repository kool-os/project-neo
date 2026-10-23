use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime};

/// Structure representing cached data with a timestamp
#[derive(Serialize, Deserialize, Debug)]
pub struct CacheEntry<T> {
    pub timestamp: u64,
    pub data: T,
}

/// Resolves the neo cache directory (~/.cache/neo or $XDG_CACHE_HOME/neo)
pub fn get_cache_dir_path() -> PathBuf {
    if let Ok(xdg) = std::env::var("XDG_CACHE_HOME") {
        if !xdg.is_empty() {
            let path = PathBuf::from(xdg).join("neo");
            let _ = fs::create_dir_all(&path);
            return path;
        }
    }

    if let Ok(home) = std::env::var("HOME") {
        let path = PathBuf::from(home).join(".cache").join("neo");
        let _ = fs::create_dir_all(&path);
        return path;
    }

    let fallback = PathBuf::from("/tmp/neo-cache");
    let _ = fs::create_dir_all(&fallback);
    fallback
}

/// Returns the cache directory path as a String
pub fn get_cache_dir() -> String {
    get_cache_dir_path().to_string_lossy().to_string()
}

/// Clears all files and directories in the cache folder
pub fn clear_cache() -> Result<bool> {
    let cache_dir = get_cache_dir_path();
    if cache_dir.exists() {
        for entry in fs::read_dir(&cache_dir).context("Failed to read cache directory")? {
            let entry = entry?;
            let path = entry.path();
            if path.is_dir() {
                fs::remove_dir_all(&path).context(format!("Failed to remove dir {:?}", path))?;
            } else {
                fs::remove_file(&path).context(format!("Failed to remove file {:?}", path))?;
            }
        }
    }
    fs::create_dir_all(&cache_dir).context("Failed to recreate cache directory")?;
    Ok(true)
}

/// Computes total size of cache in bytes
pub fn get_cache_size() -> Result<u64> {
    let cache_dir = get_cache_dir_path();
    if !cache_dir.exists() {
        return Ok(0);
    }
    compute_dir_size(&cache_dir)
}

fn compute_dir_size(path: &Path) -> Result<u64> {
    let mut total = 0;
    if path.is_dir() {
        for entry in fs::read_dir(path)? {
            let entry = entry?;
            let p = entry.path();
            if p.is_dir() {
                total += compute_dir_size(&p)?;
            } else if let Ok(meta) = entry.metadata() {
                total += meta.len();
            }
        }
    } else if let Ok(meta) = path.metadata() {
        total = meta.len();
    }
    Ok(total)
}

fn sanitize_filename(name: &str) -> String {
    name.chars()
        .map(|c| if c.is_alphanumeric() || c == '-' || c == '_' { c } else { '_' })
        .collect()
}

/// Cache a search query result
pub fn store_search_cache(backend: &str, query: &str, results: &serde_json::Value) -> Result<()> {
    let search_dir = get_cache_dir_path().join("search").join(backend);
    fs::create_dir_all(&search_dir)?;

    let filename = format!("{}.json", sanitize_filename(query));
    let file_path = search_dir.join(filename);

    let now = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap_or(Duration::from_secs(0))
        .as_secs();

    let entry = CacheEntry {
        timestamp: now,
        data: results,
    };

    let serialized = serde_json::to_string_pretty(&entry)?;
    fs::write(file_path, serialized)?;
    Ok(())
}

/// Retrieve a cached search query result if within TTL (seconds)
pub fn get_search_cache(backend: &str, query: &str, max_age_secs: u64) -> Option<serde_json::Value> {
    let search_dir = get_cache_dir_path().join("search").join(backend);
    let filename = format!("{}.json", sanitize_filename(query));
    let file_path = search_dir.join(filename);

    if !file_path.exists() {
        return None;
    }

    let content = fs::read_to_string(&file_path).ok()?;
    let entry: CacheEntry<serde_json::Value> = serde_json::from_str(&content).ok()?;

    let now = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap_or(Duration::from_secs(0))
        .as_secs();

    if now.saturating_sub(entry.timestamp) > max_age_secs {
        // Cache expired
        let _ = fs::remove_file(file_path);
        return None;
    }

    Some(entry.data)
}
