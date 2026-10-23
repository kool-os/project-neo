use serde::{Deserialize, Serialize};
use std::cmp::Ordering;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PackageAtom {
    pub raw: String,
    pub category: Option<String>,
    pub name: String,
    pub version_constraint: Option<String>,
    pub slot: Option<String>,
    pub backend: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ResolvedPackage {
    pub name: String,
    pub category: Option<String>,
    pub version: Option<String>,
    pub backend: String,
    pub is_binary: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conflict {
    pub package_a: String,
    pub package_b: String,
    pub reason: String,
}

/// Parses a package specification such as:
/// - "firefox:flatp"
/// - "firefox :flatp"
/// - ">=app-editors/vim-9.0:ebuild"
/// - "python:3.11"
/// - "app-misc/jq"
pub fn parse_atom(input: &str) -> PackageAtom {
    let trimmed = input.trim();
    let mut backend: Option<String> = None;
    let mut main_part = trimmed.to_string();

    // Check if backend alias is provided after colon or space-colon
    // E.g., "vim :ebuild" or "vim:ebuild"
    if let Some(idx) = main_part.rfind(':') {
        let suffix = &main_part[idx + 1..].trim();
        // Check if suffix matches recognized backend aliases
        if matches!(*suffix, "ebuild" | "flatp" | "brew" | "cask" | "ebins" | "flatpak" | "portage") {
            backend = Some(match *suffix {
                "flatpak" => "flatp".to_string(),
                "portage" => "ebuild".to_string(),
                other => other.to_string(),
            });
            main_part = main_part[..idx].trim().to_string();
        }
    }

    // Check version constraint prefixes (Gentoo atoms: >=, <=, =, >, <, ~)
    let mut version_constraint = None;
    let ops = ["<=", ">=", "==", "!=", "=", "<", ">", "~"];
    for op in ops {
        if main_part.starts_with(op) {
            version_constraint = Some(op.to_string());
            main_part = main_part[op.len()..].trim().to_string();
            break;
        }
    }

    // Check category: category/package
    let mut category = None;
    let mut name = main_part.clone();
    let mut slot = None;

    if let Some(slash_idx) = main_part.find('/') {
        category = Some(main_part[..slash_idx].to_string());
        name = main_part[slash_idx + 1..].to_string();
    }

    // Check slot: e.g. python:3.12 (if not already parsed as backend)
    if let Some(colon_idx) = name.find(':') {
        let s = name[colon_idx + 1..].to_string();
        name = name[..colon_idx].to_string();
        slot = Some(s);
    }

    PackageAtom {
        raw: input.to_string(),
        category,
        name,
        version_constraint,
        slot,
        backend,
    }
}

/// Resolves a package specification against available backends and a default backend.
pub fn resolve_package(
    spec: &str,
    available_backends: &[String],
    default_backend: &str,
) -> ResolvedPackage {
    let atom = parse_atom(spec);
    let chosen_backend = if let Some(ref b) = atom.backend {
        if available_backends.contains(b) {
            b.clone()
        } else {
            default_backend.to_string()
        }
    } else {
        default_backend.to_string()
    };

    let is_binary = chosen_backend == "ebins" || chosen_backend == "flatp";

    ResolvedPackage {
        name: atom.name,
        category: atom.category,
        version: None,
        backend: chosen_backend,
        is_binary,
    }
}

/// Tokenizes a version string into components (numeric or string)
#[derive(Debug, PartialEq, Eq)]
enum VerToken<'a> {
    Num(u64),
    Str(&'a str),
}

fn tokenize_version<'a>(v: &'a str) -> Vec<VerToken<'a>> {
    let mut tokens = Vec::new();
    let mut cur_num: Option<u64> = None;
    let mut cur_str = String::new();

    for c in v.chars() {
        if c.is_ascii_digit() {
            if !cur_str.is_empty() {
                tokens.push(VerToken::Str(&v[0..0])); // placeholder or flush
                cur_str.clear();
            }
            cur_num = Some(cur_num.unwrap_or(0) * 10 + (c as u64 - '0' as u64));
        } else if c == '.' || c == '-' || c == '_' {
            if let Some(n) = cur_num {
                tokens.push(VerToken::Num(n));
                cur_num = None;
            }
        } else {
            if let Some(n) = cur_num {
                tokens.push(VerToken::Num(n));
                cur_num = None;
            }
            cur_str.push(c);
        }
    }
    if let Some(n) = cur_num {
        tokens.push(VerToken::Num(n));
    }
    tokens
}

/// Compares two package versions (e.g. "1.10.2" vs "1.9.5")
pub fn compare_versions(v1: &str, v2: &str) -> Ordering {
    let t1 = tokenize_version(v1);
    let t2 = tokenize_version(v2);

    let len = t1.len().max(t2.len());
    for i in 0..len {
        let tok1 = t1.get(i);
        let tok2 = t2.get(i);

        match (tok1, tok2) {
            (Some(VerToken::Num(a)), Some(VerToken::Num(b))) => {
                if a != b {
                    return a.cmp(b);
                }
            }
            (Some(VerToken::Num(a)), None) => {
                if *a > 0 {
                    return Ordering::Greater;
                }
            }
            (None, Some(VerToken::Num(b))) => {
                if *b > 0 {
                    return Ordering::Less;
                }
            }
            _ => {}
        }
    }
    Ordering::Equal
}

/// Simple conflict check between requested packages
pub fn detect_conflicts(requested: &[PackageAtom]) -> Vec<Conflict> {
    let mut conflicts = Vec::new();
    for i in 0..requested.len() {
        for j in (i + 1)..requested.len() {
            let a = &requested[i];
            let b = &requested[j];

            // Same package name targeted to different backends
            if a.name == b.name && a.backend != b.backend && a.backend.is_some() && b.backend.is_some() {
                conflicts.push(Conflict {
                    package_a: a.raw.clone(),
                    package_b: b.raw.clone(),
                    reason: format!(
                        "Package '{}' specified on both :{} and :{}",
                        a.name,
                        a.backend.as_ref().unwrap(),
                        b.backend.as_ref().unwrap()
                    ),
                });
            }
        }
    }
    conflicts
}
