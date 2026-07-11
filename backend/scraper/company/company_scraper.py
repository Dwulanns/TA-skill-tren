#!/usr/bin/env python3
"""
Minimal company scraper using requests + BeautifulSoup focused on extracting
employee size from a LinkedIn company page (static HTML). Designed for
clean separation from enrichment orchestration.
"""
from __future__ import annotations

import json
import re
from typing import Optional

import requests
from bs4 import BeautifulSoup


class CompanyScraper:
	USER_AGENT = (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
		"(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
	)

	SIZE_TOKEN = r"(?:\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?[kKmM]?)"
	RANGE_TOKEN = rf"{SIZE_TOKEN}(?:\s*[-–]\s*{SIZE_TOKEN})?\+?"

	LIMITED_PAGE_MARKERS = (
		"join linkedin",
		"sign in",
		"security verification",
		"let's do a quick security check",
		"challenge",
		"captcha",
	)

	EMPLOYEE_PATTERNS = [
		re.compile(
			rf"(?:ukuran perusahaan|company size|jumlah karyawan|number of employees|employee count|headcount)\s*[:\-]?\s*(?P<size>{RANGE_TOKEN})\s*(?:karyawan|employees?)?",
			re.I,
		),
		re.compile(
			rf"(?P<size>{RANGE_TOKEN})\s*(?:karyawan|employees?)\s*(?:\[[^\]]*\]|\([^\)]*\))?",
			re.I,
		),
		re.compile(rf"(?P<size>{RANGE_TOKEN})\s*(?:karyawan|employees?)", re.I),
		re.compile(r"company\s*size[:\s]+(?P<size>[^\n\r<]{2,100})", re.I),
	]

	def __init__(self) -> None:
		self.session = requests.Session()
		self.session.headers.update(
			{
				"User-Agent": self.USER_AGENT,
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
				"Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
			}
		)

	@staticmethod
	def _normalize_text(value: str) -> str:
		cleaned = (value or "").replace("\u2013", "-").replace("\u2014", "-").replace("\xa0", " ")
		return re.sub(r"\s+", " ", cleaned).strip()

	@classmethod
	def _is_limited_page_text(cls, text: str) -> bool:
		lowered = cls._normalize_text(text).lower()
		if not lowered:
			return True
		if any(marker in lowered for marker in cls.LIMITED_PAGE_MARKERS):
			return True
		# Some blocked pages return almost empty body with generic LinkedIn shell.
		if len(lowered) < 120 and "linkedin" in lowered:
			return True
		return False

	@classmethod
	def _normalize_employee_size_value(cls, value: str) -> Optional[str]:
		normalized = cls._normalize_text(value)
		if not normalized:
			return None

		normalized = re.sub(r"\s+employees?$", "", normalized, flags=re.I).strip()
		normalized = re.sub(r"\s+karyawan$", "", normalized, flags=re.I).strip()
		normalized = re.sub(r"\s*\+\s*$", "+", normalized).strip()
		return normalized or None

	def get_page_text(self, url: str, timeout: int = 20) -> Optional[str]:
		try:
			resp = self.session.get(url, timeout=timeout)
			if not resp.ok:
				return None
			soup = BeautifulSoup(resp.text, "html.parser")
			text = self._normalize_text(soup.get_text(" ", strip=True))
			if self._is_limited_page_text(text):
				return None
			return text
		except Exception:
			return None

	def get_page_soup(self, url: str, timeout: int = 20) -> Optional[BeautifulSoup]:
		try:
			resp = self.session.get(url, timeout=timeout)
			if not resp.ok:
				return None
			soup = BeautifulSoup(resp.text, "html.parser")
			if self._is_limited_page_text(soup.get_text(" ", strip=True)):
				return None
			return soup
		except Exception:
			return None

	def extract_employee_size_from_soup(self, soup: BeautifulSoup) -> Optional[str]:
		if soup is None:
			return None

		# 1) Structured JSON-LD metadata.
		try:
			for script in soup.find_all("script", type="application/ld+json"):
				raw = (script.string or script.get_text(strip=True) or "").strip()
				if not raw:
					continue

				try:
					data = json.loads(raw)
				except Exception:
					continue

				candidates = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
				for obj in candidates:
					if not isinstance(obj, dict):
						continue
					for key in ("numberOfEmployees", "employees", "member", "memberCount"):
						if key not in obj:
							continue
						value = obj.get(key)
						if isinstance(value, (int, float)):
							return str(int(value)) if float(value).is_integer() else str(value)
						if isinstance(value, str) and value.strip():
							normalized = self._normalize_employee_size_value(value)
							if normalized:
								return normalized
		except Exception:
			pass

		# 2) Visible text on the page.
		page_text = self._normalize_text(soup.get_text(" ", strip=True))
		return self.extract_employee_size_from_text(page_text)

	def extract_employee_size_from_text(self, text: str) -> Optional[str]:
		normalized_text = self._normalize_text(text)
		if not normalized_text or self._is_limited_page_text(normalized_text):
			return None

		for pattern in self.EMPLOYEE_PATTERNS:
			match = pattern.search(normalized_text)
			if match:
				size = self._normalize_employee_size_value(match.group("size"))
				if size:
					return size

		return None


__all__ = ["CompanyScraper"]