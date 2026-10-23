pub mod cache;
pub mod downloader;
pub mod resolver;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub name: String,
    pub version: String,
    pub description: String,
    pub backend: String,
    pub installed: bool,
    #[serde(default)]
    pub homepage: String,
    #[serde(default)]
    pub category: String,
}

fn search_portage_internal(query: &str, backend: &str) -> Vec<SearchResult> {
    let repo_path = Path::new("/var/db/repos/gentoo");
    let installed_db = Path::new("/var/db/pkg");
    let query_lower = query.to_lowercase();
    let mut results: Vec<SearchResult> = Vec::new();

    if !repo_path.exists() {
        return results;
    }

    // Categories are directories not starting with '.' or metadata/profiles/eclass/licenses
    let categories: Vec<PathBuf> = match fs::read_dir(repo_path) {
        Ok(read_dir) => read_dir
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| {
                if !p.is_dir() {
                    return false;
                }
                if let Some(name) = p.file_name().and_then(|n| n.to_str()) {
                    !name.starts_with('.')
                        && name != "metadata"
                        && name != "profiles"
                        && name != "eclass"
                        && name != "licenses"
                        && name != "packages"
                        && name != "distfiles"
                        && name.contains('-') // Gentoo categories typically have hyphens (app-*, dev-*, etc.)
                } else {
                    false
                }
            })
            .collect(),
        Err(_) => return results,
    };

    let matched_packages: Vec<SearchResult> = categories
        .par_iter()
        .flat_map(|cat_dir| {
            let cat_name = cat_dir.file_name().unwrap().to_string_lossy().to_string();
            let mut cat_matches = Vec::new();

            if let Ok(entries) = fs::read_dir(cat_dir) {
                for pkg_entry in entries.flatten() {
                    let pkg_path = pkg_entry.path();
                    if !pkg_path.is_dir() {
                        continue;
                    }
                    let pkg_name = pkg_path.file_name().unwrap().to_string_lossy().to_string();
                    let full_name = format!("{}/{}", cat_name, pkg_name);

                    // Search match on package name or full atom
                    if pkg_name.to_lowercase().contains(&query_lower)
                        || full_name.to_lowercase().contains(&query_lower)
                    {
                        // Extract latest version and description from ebuilds
                        let mut latest_version = "unknown".to_string();
                        let mut desc = String::new();
                        let mut homepage = String::new();

                        if let Ok(ebuilds) = fs::read_dir(&pkg_path) {
                            let mut ebuild_files: Vec<String> = ebuilds
                                .flatten()
                                .filter_map(|e| {
                                    let fname = e.file_name().to_string_lossy().to_string();
                                    if fname.ends_with(".ebuild") {
                                        Some(fname)
                                    } else {
                                        None
                                    }
                                })
                                .collect();

                            ebuild_files.sort();
                            if let Some(latest_ebuild) = ebuild_files.last() {
                                // e.g. vim-9.1.0700.ebuild -> version
                                let base = latest_ebuild.trim_end_matches(".ebuild");
                                if base.starts_with(&pkg_name) {
                                    let v_part = &base[pkg_name.len()..];
                                    latest_version = v_part.trim_start_matches('-').to_string();
                                } else {
                                    latest_version = base.to_string();
                                }

                                // Quick inspect ebuild for DESCRIPTION and HOMEPAGE
                                let ebuild_path = pkg_path.join(latest_ebuild);
                                if let Ok(content) = fs::read_to_string(ebuild_path) {
                                    for line in content.lines() {
                                        let trimmed = line.trim();
                                        if trimmed.starts_with("DESCRIPTION=") && desc.is_empty() {
                                            let val = trimmed.trim_start_matches("DESCRIPTION=");
                                            desc = val.trim_matches('"').trim_matches('\'').to_string();
                                        } else if trimmed.starts_with("HOMEPAGE=") && homepage.is_empty() {
                                            let val = trimmed.trim_start_matches("HOMEPAGE=");
                                            homepage = val.trim_matches('"').trim_matches('\'').to_string();
                                        }
                                    }
                                }
                            }
                        }

                        // Check if installed in /var/db/pkg/<cat>/<pkg>-<version>
                        let mut installed = false;
                        let installed_cat = installed_db.join(&cat_name);
                        if installed_cat.exists() {
                            if let Ok(inst_entries) = fs::read_dir(installed_cat) {
                                for inst_entry in inst_entries.flatten() {
                                    let inst_name = inst_entry.file_name().to_string_lossy().to_string();
                                    if inst_name.starts_with(&format!("{}-", pkg_name)) {
                                        installed = true;
                                        break;
                                    }
                                }
                            }
                        }

                        cat_matches.push(SearchResult {
                            name: full_name,
                            version: latest_version,
                            description: desc,
                            backend: backend.to_string(),
                            installed,
                            homepage,
                            category: cat_name.clone(),
                        });
                    }
                }
            }
            cat_matches
        })
        .collect();

    results.extend(matched_packages);
    results.truncate(50); // Keep top results
    results
}

fn search_flatpak_internal(query: &str) -> Vec<SearchResult> {
    let mut results = Vec::new();
    let output = Command::new("flatpak")
        .args(["search", query, "--columns=name,application,version,description"])
        .output();

    if let Ok(out) = output {
        if out.status.success() {
            let text = String::from_utf8_lossy(&out.stdout);
            for line in text.lines().skip(1) {
                let parts: Vec<&str> = line.split('\t').collect();
                if parts.len() >= 4 {
                    let app_id = parts[1].trim();
                    results.push(SearchResult {
                        name: if app_id.is_empty() { parts[0].trim().to_string() } else { app_id.to_string() },
                        version: parts[2].trim().to_string(),
                        description: parts[3].trim().to_string(),
                        backend: "flatp".to_string(),
                        installed: false,
                        homepage: String::new(),
                        category: "flatpak".to_string(),
                    });
                }
            }
        }
    }
    results
}

fn search_brew_internal(query: &str, is_cask: bool) -> Vec<SearchResult> {
    let mut results = Vec::new();
    let backend_name = if is_cask { "cask" } else { "brew" };
    let brew_cmd = "/home/linuxbrew/.linuxbrew/bin/brew";

    let mut args = vec!["search"];
    if is_cask {
        args.push("--cask");
    }
    args.push(query);

    let output = Command::new(brew_cmd).args(&args).output();

    if let Ok(out) = output {
        if out.status.success() {
            let text = String::from_utf8_lossy(&out.stdout);
            for line in text.lines() {
                let trimmed = line.trim();
                if trimmed.is_empty() || trimmed.starts_with("==>") {
                    continue;
                }
                for item in trimmed.split_whitespace() {
                    results.push(SearchResult {
                        name: item.to_string(),
                        version: "latest".to_string(),
                        description: format!("Homebrew {} formula", backend_name),
                        backend: backend_name.to_string(),
                        installed: false,
                        homepage: String::new(),
                        category: backend_name.to_string(),
                    });
                }
            }
        }
    }
    results
}

pub fn search_internal(query: &str, backend: &str) -> Vec<SearchResult> {
    // Check cache
    if let Some(cached_val) = cache::get_search_cache(backend, query, 300) {
        if let Ok(parsed) = serde_json::from_value::<Vec<SearchResult>>(cached_val) {
            return parsed;
        }
    }

    let results = match backend {
        "ebuild" | "ebins" => search_portage_internal(query, backend),
        "flatp" | "flatpak" => search_flatpak_internal(query),
        "brew" => search_brew_internal(query, false),
        "cask" => search_brew_internal(query, true),
        _ => Vec::new(),
    };

    if let Ok(val) = serde_json::to_value(&results) {
        let _ = cache::store_search_cache(backend, query, &val);
    }

    results
}

/// Expose search_package to Python
#[pyfunction]
pub fn search_package(py: Python, name: String, backend: String) -> PyResult<PyObject> {
    let results = search_internal(&name, &backend);
    let py_list = PyList::empty_bound(py);

    for item in results {
        let dict = PyDict::new_bound(py);
        dict.set_item("name", item.name)?;
        dict.set_item("version", item.version)?;
        dict.set_item("description", item.description)?;
        dict.set_item("backend", item.backend)?;
        dict.set_item("installed", item.installed)?;
        dict.set_item("homepage", item.homepage)?;
        dict.set_item("category", item.category)?;
        py_list.append(dict)?;
    }

    Ok(py_list.into())
}

/// Expose download_package to Python
#[pyfunction]
pub fn download_package(url: String, dest: String) -> PyResult<bool> {
    match downloader::download_sync(&url, &dest) {
        Ok(success) => Ok(success),
        Err(_) => Ok(false),
    }
}

/// Expose get_cache_dir to Python
#[pyfunction]
pub fn get_cache_dir() -> PyResult<String> {
    Ok(cache::get_cache_dir())
}

/// Expose clear_cache to Python
#[pyfunction]
pub fn clear_cache() -> PyResult<bool> {
    Ok(cache::clear_cache().unwrap_or(false))
}

/// Expose parallel_search to Python:
/// parallel_search(queries: list[str], backends: list[str]) -> dict
#[pyfunction]
pub fn parallel_search(
    py: Python,
    queries: Vec<String>,
    backends: Vec<String>,
) -> PyResult<PyObject> {
    // Generate pairs of (query, backend)
    let mut pairs = Vec::new();
    for q in &queries {
        for b in &backends {
            pairs.push((q.clone(), b.clone()));
        }
    }

    // Parallel search across all pairs
    let search_results: Vec<((String, String), Vec<SearchResult>)> = pairs
        .par_iter()
        .map(|(q, b)| {
            let res = search_internal(q, b);
            ((q.clone(), b.clone()), res)
        })
        .collect();

    let root_dict = PyDict::new_bound(py);

    // If there is only one query, provide root_dict[backend] = list
    // AND root_dict[query] = {backend: list}
    if queries.len() == 1 {
        let single_q = &queries[0];
        let sub_dict = PyDict::new_bound(py);

        for ((_, b), items) in &search_results {
            let list = PyList::empty_bound(py);
            for item in items {
                let dict = PyDict::new_bound(py);
                dict.set_item("name", &item.name)?;
                dict.set_item("version", &item.version)?;
                dict.set_item("description", &item.description)?;
                dict.set_item("backend", &item.backend)?;
                dict.set_item("installed", item.installed)?;
                dict.set_item("homepage", &item.homepage)?;
                dict.set_item("category", &item.category)?;
                list.append(dict)?;
            }
            root_dict.set_item(b, &list)?;
            sub_dict.set_item(b, &list)?;
        }
        root_dict.set_item(single_q, sub_dict)?;
    } else {
        // Multiple queries: organize by query -> backend -> list
        for q in &queries {
            let query_dict = PyDict::new_bound(py);
            for b in &backends {
                let list = PyList::empty_bound(py);
                for ((res_q, res_b), items) in &search_results {
                    if res_q == q && res_b == b {
                        for item in items {
                            let dict = PyDict::new_bound(py);
                            dict.set_item("name", &item.name)?;
                            dict.set_item("version", &item.version)?;
                            dict.set_item("description", &item.description)?;
                            dict.set_item("backend", &item.backend)?;
                            dict.set_item("installed", item.installed)?;
                            dict.set_item("homepage", &item.homepage)?;
                            dict.set_item("category", &item.category)?;
                            list.append(dict)?;
                        }
                    }
                }
                query_dict.set_item(b, list)?;
            }
            root_dict.set_item(q, query_dict)?;
        }
    }

    Ok(root_dict.into())
}

/// PyO3 neo_core module definition
#[pymodule]
fn neo_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search_package, m)?)?;
    m.add_function(wrap_pyfunction!(download_package, m)?)?;
    m.add_function(wrap_pyfunction!(get_cache_dir, m)?)?;
    m.add_function(wrap_pyfunction!(clear_cache, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_search, m)?)?;
    Ok(())
}
