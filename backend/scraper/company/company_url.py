"""Shared helpers for LinkedIn company URL resolution and slug handling."""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import unquote, urlparse


CORPORATE_SUFFIXES = {
	"bv",
	"co",
	"co.",
	"corp",
	"corporation",
	"cv",
	"cv.",
	"gmbh",
	"inc",
	"inc.",
	"llc",
	"ltd",
	"ltd.",
	"plc",
	"pt",
	"pt.",
	"pte",
	"pte.",
	"sa",
	"sdn",
	"spa",
	"tbk",
	"persero",
}

REGIONAL_KEYWORDS = {
	"asia",
	"china",
	"emea",
	"hong kong",
	"india",
	"indonesia",
	"japan",
	"korea",
	"malaysia",
	"philippines",
	"singapore",
	"south east asia",
	"southeast asia",
	"thailand",
	"taiwan",
	"vietnam",
}

IGNORED_TOKENS = {
	"by",
	"official",
	"the",
	"and",
	"of",
}


def normalize_text(value: str) -> str:
	return re.sub(r"\s+", " ", (value or "")).strip()


def tokenize_company_name(value: str) -> list[str]:
	return [token for token in re.split(r"[^a-z0-9]+", normalize_text(value).lower()) if token]


def extract_company_slug(company_url: str) -> str:
	parsed = urlparse(company_url)
	if not parsed.path.startswith("/company/"):
		return ""
	return parsed.path.rstrip("/").split("/company/")[-1].strip().lower()


def split_company_name_variants(company_name: str) -> list[str]:
	"""Build robust name variants from aliases and separators used in company names."""
	base_name = normalize_text(company_name)
	variants: list[str] = []

	def add_variant(value: str) -> None:
		candidate = normalize_text(value)
		if candidate and candidate not in variants:
			variants.append(candidate)

	add_variant(base_name)

	for part in re.split(r"\s*[|/]\s*", base_name):
		add_variant(part)

	for bracket_text in re.findall(r"\(([^\)]+)\)", base_name):
		add_variant(bracket_text)

	for compact in (re.sub(r"\([^\)]*\)", " ", base_name), base_name.replace("-", " ")):
		add_variant(compact)

	# Preserve acronym candidates (e.g. APP, BCA, EY) for exact slug hits.
	for token in re.findall(r"\b[A-Z]{2,8}\b", company_name):
		add_variant(token)

	return variants


def strip_company_suffixes(company_name: str) -> str:
	"""Remove legal suffixes while preserving branded/location tokens."""
	tokens = tokenize_company_name(company_name)
	if not tokens:
		return normalize_text(company_name)

	while tokens and tokens[0] in CORPORATE_SUFFIXES:
		tokens.pop(0)
	while tokens and tokens[-1] in CORPORATE_SUFFIXES:
		tokens.pop()

	return " ".join(tokens) or normalize_text(company_name)


def slugify_company_name(value: str) -> str:
	cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", normalize_text(value).lower())
	cleaned = re.sub(r"-+", "-", cleaned).strip("-")
	return cleaned


def extract_linkedin_company_url(url: str) -> Optional[str]:
	if not url:
		return None

	decoded_url = unquote(url)
	match = re.search(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/company/[\w\-_/%.]+", decoded_url, re.I)
	if not match:
		return None

	parsed = urlparse(match.group(0))
	path = parsed.path.rstrip("/")
	if not path.startswith("/company/"):
		return None

	return f"https://www.linkedin.com{path}/"


def build_company_slug_candidates(company_name: str) -> list[str]:
	candidates: list[str] = []
	for variant in split_company_name_variants(company_name):
		for candidate_name in (strip_company_suffixes(variant), normalize_text(variant)):
			slug = slugify_company_name(candidate_name)
			if slug and slug not in candidates:
				candidates.append(slug)
	return candidates


def is_regional_company_name(company_name: str) -> bool:
	normalized_name = normalize_text(company_name).lower()
	return any(keyword in normalized_name for keyword in REGIONAL_KEYWORDS)


def looks_like_company_match(company_url: str, company_name: str, response_text: str) -> bool:
	"""Validate that a LinkedIn company page matches the requested company name."""
	if not company_url or not response_text:
		return False

	normalized_text = normalize_text(response_text).lower()
	if not normalized_text:
		return False
	if "page not found" in normalized_text or "404" in normalized_text:
		return False

	parsed = urlparse(company_url)
	if not parsed.path.startswith("/company/"):
		return False

	company_slug = extract_company_slug(company_url)
	slug_text = normalize_text(company_slug.replace("-", " ").replace("_", " ").replace("/", " ")).lower()
	name_tokens = [
		token
		for token in tokenize_company_name(company_name)
		if token not in CORPORATE_SUFFIXES and token not in IGNORED_TOKENS and len(token) > 1
	]
	if not name_tokens:
		return False

	regional_tokens = [keyword for keyword in REGIONAL_KEYWORDS if keyword in normalize_text(company_name).lower()]
	overlap_count = sum(1 for token in name_tokens if token in normalized_text or token in slug_text)

	if regional_tokens:
		regional_match = any(keyword in normalized_text or keyword in slug_text for keyword in regional_tokens)
		return overlap_count >= len(name_tokens) and regional_match

	return overlap_count >= max(1, len(name_tokens) - 1)


def slug_looks_like_company(company_url: str, company_name: str) -> bool:
	"""Fallback validation when LinkedIn blocks page content (status 999/429/403)."""
	company_slug = extract_company_slug(company_url)
	if not company_slug:
		return False

	slug_tokens = [token for token in re.split(r"[^a-z0-9]+", company_slug.lower()) if token]
	primary_name = normalize_text(re.split(r"\s*[|/]\s*", company_name, maxsplit=1)[0])
	primary_tokens = [
		token
		for token in tokenize_company_name(primary_name)
		if token not in CORPORATE_SUFFIXES and token not in IGNORED_TOKENS and len(token) > 1
	]
	if primary_tokens and not any(token in slug_tokens for token in primary_tokens):
		return False

	for variant in split_company_name_variants(company_name):
		name_tokens = [
			token
			for token in tokenize_company_name(variant)
			if token not in CORPORATE_SUFFIXES and token not in IGNORED_TOKENS and len(token) > 1
		]
		if not name_tokens:
			continue

		overlap = sum(1 for token in name_tokens if token in slug_tokens)
		if is_regional_company_name(variant):
			if overlap >= len(name_tokens):
				return True
			continue

		# Accept if one strong alias variant matches (e.g. "Devoteam" from "Devoteam | Google Cloud Partner").
		if overlap >= max(1, len(name_tokens) - 1):
			return True

	return False


__all__ = [
	"CORPORATE_SUFFIXES",
	"REGIONAL_KEYWORDS",
	"build_company_slug_candidates",
	"extract_linkedin_company_url",
	"is_regional_company_name",
	"looks_like_company_match",
	"normalize_text",
	"slug_looks_like_company",
	"slugify_company_name",
	"split_company_name_variants",
	"strip_company_suffixes",
]