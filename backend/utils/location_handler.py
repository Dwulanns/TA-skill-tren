"""
location_handler.py — Location Normalization with Indonesian City/Province Data
"""

from __future__ import annotations

import re
from typing import Optional, Dict, Set, List, Tuple
from dataclasses import dataclass
from enum import Enum


class LocationType(Enum):
    CITY = "city"
    REGENCY = "regency"
    PROVINCE = "province"
    OTHER = "other"
    INDONESIA = "indonesia"


@dataclass
class LocationResult:
    normalized: str
    original: str
    location_type: LocationType
    confidence: float = 1.0


class KabupatenData:
    KABUPATEN_TO_PROVINSI = {
        "SIMEULUE": "ACEH","ACEH SINGKIL": "ACEH","ACEH SELATAN": "ACEH","ACEH TENGGARA": "ACEH",
        "ACEH TIMUR": "ACEH","ACEH TENGAH": "ACEH","ACEH BARAT": "ACEH","ACEH BESAR": "ACEH",
        "PIDIE": "ACEH","BIREUEN": "ACEH","ACEH UTARA": "ACEH","ACEH BARAT DAYA": "ACEH",
        "GAYO LUES": "ACEH","ACEH TAMIANG": "ACEH","NAGAN RAYA": "ACEH","ACEH JAYA": "ACEH",
        "BENER MERIAH": "ACEH","PIDIE JAYA": "ACEH","BANDA ACEH": "ACEH","SABANG": "ACEH",
        "LANGSA": "ACEH","LHOKSEUMAWE": "ACEH","SUBULUSSALAM": "ACEH",
        "NIAS": "SUMATERA UTARA","MANDAILING NATAL": "SUMATERA UTARA","TAPANULI SELATAN": "SUMATERA UTARA",
        "TAPANULI TENGAH": "SUMATERA UTARA","TAPANULI UTARA": "SUMATERA UTARA","TOBA SAMOSIR": "SUMATERA UTARA",
        "LABUHAN BATU": "SUMATERA UTARA","ASAHAN": "SUMATERA UTARA","SIMALUNGUN": "SUMATERA UTARA",
        "DAIRI": "SUMATERA UTARA","KARO": "SUMATERA UTARA","DELI SERDANG": "SUMATERA UTARA",
        "LANGKAT": "SUMATERA UTARA","NIAS SELATAN": "SUMATERA UTARA","HUMBANG HASUNDUTAN": "SUMATERA UTARA",
        "PAKPAK BHARAT": "SUMATERA UTARA","SAMOSIR": "SUMATERA UTARA","SERDANG BEDAGAI": "SUMATERA UTARA",
        "BATU BARA": "SUMATERA UTARA","PADANG LAWAS UTARA": "SUMATERA UTARA","PADANG LAWAS": "SUMATERA UTARA",
        "LABUHAN BATU SELATAN": "SUMATERA UTARA","LABUHAN BATU UTARA": "SUMATERA UTARA",
        "NIAS UTARA": "SUMATERA UTARA","NIAS BARAT": "SUMATERA UTARA","SIBOLGA": "SUMATERA UTARA",
        "TANJUNG BALAI": "SUMATERA UTARA","PEMATANG SIANTAR": "SUMATERA UTARA","TEBING TINGGI": "SUMATERA UTARA",
        "MEDAN": "SUMATERA UTARA","BINJAI": "SUMATERA UTARA","PADANGSIDIMPUAN": "SUMATERA UTARA",
        "GUNUNGSITOLI": "SUMATERA UTARA",
        "KEPULAUAN MENTAWAI": "SUMATERA BARAT","PESISIR SELATAN": "SUMATERA BARAT","SOLOK": "SUMATERA BARAT",
        "SIJUNJUNG": "SUMATERA BARAT","TANAH DATAR": "SUMATERA BARAT","PADANG PARIAMAN": "SUMATERA BARAT",
        "AGAM": "SUMATERA BARAT","LIMA PULUH KOTA": "SUMATERA BARAT","PASAMAN": "SUMATERA BARAT",
        "SOLOK SELATAN": "SUMATERA BARAT","DHARMASRAYA": "SUMATERA BARAT","PASAMAN BARAT": "SUMATERA BARAT",
        "PADANG": "SUMATERA BARAT","SAWAH LUNTO": "SUMATERA BARAT","PADANG PANJANG": "SUMATERA BARAT",
        "BUKITTINGGI": "SUMATERA BARAT","PAYAKUMBUH": "SUMATERA BARAT","PARIAMAN": "SUMATERA BARAT",
        "KUANTAN SINGINGI": "RIAU","INDRAGIRI HULU": "RIAU","INDRAGIRI HILIR": "RIAU",
        "PELALAWAN": "RIAU","SIAK": "RIAU","KAMPAR": "RIAU","ROKAN HULU": "RIAU",
        "BENGKALIS": "RIAU","ROKAN HILIR": "RIAU","KEPULAUAN MERANTI": "RIAU",
        "PEKANBARU": "RIAU","DUMAI": "RIAU",
        "KERINCI": "JAMBI","MERANGIN": "JAMBI","SAROLANGUN": "JAMBI","BATANG HARI": "JAMBI",
        "MUARO JAMBI": "JAMBI","TANJUNG JABUNG TIMUR": "JAMBI","TANJUNG JABUNG BARAT": "JAMBI",
        "TEBO": "JAMBI","BUNGO": "JAMBI","JAMBI": "JAMBI","SUNGAI PENUH": "JAMBI",
        "OGAN KOMERING ULU": "SUMATERA SELATAN","OGAN KOMERING ILIR": "SUMATERA SELATAN",
        "MUARA ENIM": "SUMATERA SELATAN","LAHAT": "SUMATERA SELATAN","MUSI RAWAS": "SUMATERA SELATAN",
        "MUSI BANYUASIN": "SUMATERA SELATAN","BANYU ASIN": "SUMATERA SELATAN",
        "OGAN KOMERING ULU SELATAN": "SUMATERA SELATAN","OGAN KOMERING ULU TIMUR": "SUMATERA SELATAN",
        "OGAN ILIR": "SUMATERA SELATAN","EMPAT LAWANG": "SUMATERA SELATAN",
        "PENUKAL ABAB LEMATANG ILIR": "SUMATERA SELATAN","MUSI RAWAS UTARA": "SUMATERA SELATAN",
        "PALEMBANG": "SUMATERA SELATAN","PRABUMULIH": "SUMATERA SELATAN",
        "PAGAR ALAM": "SUMATERA SELATAN","LUBUKLINGGAU": "SUMATERA SELATAN",
        "BENGKULU SELATAN": "BENGKULU","REJANG LEBONG": "BENGKULU","BENGKULU UTARA": "BENGKULU",
        "KAUR": "BENGKULU","SELUMA": "BENGKULU","MUKOMUKO": "BENGKULU","LEBONG": "BENGKULU",
        "KEPAHIANG": "BENGKULU","BENGKULU TENGAH": "BENGKULU","BENGKULU": "BENGKULU",
        "LAMPUNG BARAT": "LAMPUNG","TANGGAMUS": "LAMPUNG","LAMPUNG SELATAN": "LAMPUNG",
        "LAMPUNG TIMUR": "LAMPUNG","LAMPUNG TENGAH": "LAMPUNG","LAMPUNG UTARA": "LAMPUNG",
        "WAY KANAN": "LAMPUNG","TULANGBAWANG": "LAMPUNG","PESAWARAN": "LAMPUNG",
        "PRINGSEWU": "LAMPUNG","MESUJI": "LAMPUNG","TULANG BAWANG BARAT": "LAMPUNG",
        "PESISIR BARAT": "LAMPUNG","BANDAR LAMPUNG": "LAMPUNG","METRO": "LAMPUNG",
        "BANGKA": "KEPULAUAN BANGKA BELITUNG","BELITUNG": "KEPULAUAN BANGKA BELITUNG",
        "BANGKA BARAT": "KEPULAUAN BANGKA BELITUNG","BANGKA TENGAH": "KEPULAUAN BANGKA BELITUNG",
        "BANGKA SELATAN": "KEPULAUAN BANGKA BELITUNG","BELITUNG TIMUR": "KEPULAUAN BANGKA BELITUNG",
        "PANGKAL PINANG": "KEPULAUAN BANGKA BELITUNG",
        "KARIMUN": "KEPULAUAN RIAU","BINTAN": "KEPULAUAN RIAU","NATUNA": "KEPULAUAN RIAU",
        "LINGGA": "KEPULAUAN RIAU","KEPULAUAN ANAMBAS": "KEPULAUAN RIAU",
        "BATAM": "KEPULAUAN RIAU","TANJUNG PINANG": "KEPULAUAN RIAU",
        "KEPULAUAN SERIBU": "DKI JAKARTA","JAKARTA SELATAN": "DKI JAKARTA",
        "JAKARTA TIMUR": "DKI JAKARTA","JAKARTA PUSAT": "DKI JAKARTA",
        "JAKARTA BARAT": "DKI JAKARTA","JAKARTA UTARA": "DKI JAKARTA",
        "BOGOR": "JAWA BARAT","SUKABUMI": "JAWA BARAT","CIANJUR": "JAWA BARAT",
        "BANDUNG": "JAWA BARAT","GARUT": "JAWA BARAT","TASIKMALAYA": "JAWA BARAT",
        "CIAMIS": "JAWA BARAT","KUNINGAN": "JAWA BARAT","CIREBON": "JAWA BARAT",
        "MAJALENGKA": "JAWA BARAT","SUMEDANG": "JAWA BARAT","INDRAMAYU": "JAWA BARAT",
        "SUBANG": "JAWA BARAT","PURWAKARTA": "JAWA BARAT","KARAWANG": "JAWA BARAT",
        "BEKASI": "JAWA BARAT","BANDUNG BARAT": "JAWA BARAT","PANGANDARAN": "JAWA BARAT",
        "DEPOK": "JAWA BARAT","CIMAHI": "JAWA BARAT","BANJAR": "JAWA BARAT",
        "CILACAP": "JAWA TENGAH","BANYUMAS": "JAWA TENGAH","PURBALINGGA": "JAWA TENGAH",
        "BANJARNEGARA": "JAWA TENGAH","KEBUMEN": "JAWA TENGAH","PURWOREJO": "JAWA TENGAH",
        "WONOSOBO": "JAWA TENGAH","MAGELANG": "JAWA TENGAH","BOYOLALI": "JAWA TENGAH",
        "KLATEN": "JAWA TENGAH","SUKOHARJO": "JAWA TENGAH","WONOGIRI": "JAWA TENGAH",
        "KARANGANYAR": "JAWA TENGAH","SRAGEN": "JAWA TENGAH","GROBOGAN": "JAWA TENGAH",
        "BLORA": "JAWA TENGAH","REMBANG": "JAWA TENGAH","PATI": "JAWA TENGAH",
        "KUDUS": "JAWA TENGAH","JEPARA": "JAWA TENGAH","DEMAK": "JAWA TENGAH",
        "SEMARANG": "JAWA TENGAH","TEMANGGUNG": "JAWA TENGAH","KENDAL": "JAWA TENGAH",
        "BATANG": "JAWA TENGAH","PEKALONGAN": "JAWA TENGAH","PEMALANG": "JAWA TENGAH",
        "TEGAL": "JAWA TENGAH","BREBES": "JAWA TENGAH","SURAKARTA": "JAWA TENGAH",
        "SALATIGA": "JAWA TENGAH",
        "KULON PROGO": "DI YOGYAKARTA","BANTUL": "DI YOGYAKARTA","GUNUNG KIDUL": "DI YOGYAKARTA",
        "SLEMAN": "DI YOGYAKARTA","YOGYAKARTA": "DI YOGYAKARTA",
        "PACITAN": "JAWA TIMUR","PONOROGO": "JAWA TIMUR","TRENGGALEK": "JAWA TIMUR",
        "TULUNGAGUNG": "JAWA TIMUR","BLITAR": "JAWA TIMUR","KEDIRI": "JAWA TIMUR",
        "MALANG": "JAWA TIMUR","LUMAJANG": "JAWA TIMUR","JEMBER": "JAWA TIMUR",
        "BANYUWANGI": "JAWA TIMUR","BONDOWOSO": "JAWA TIMUR","SITUBONDO": "JAWA TIMUR",
        "PROBOLINGGO": "JAWA TIMUR","PASURUAN": "JAWA TIMUR","SIDOARJO": "JAWA TIMUR",
        "MOJOKERTO": "JAWA TIMUR","JOMBANG": "JAWA TIMUR","NGANJUK": "JAWA TIMUR",
        "MADIUN": "JAWA TIMUR","MAGETAN": "JAWA TIMUR","NGAWI": "JAWA TIMUR",
        "BOJONEGORO": "JAWA TIMUR","TUBAN": "JAWA TIMUR","LAMONGAN": "JAWA TIMUR",
        "GRESIK": "JAWA TIMUR","BANGKALAN": "JAWA TIMUR","SAMPANG": "JAWA TIMUR",
        "PAMEKASAN": "JAWA TIMUR","SUMENEP": "JAWA TIMUR","SURABAYA": "JAWA TIMUR","BATU": "JAWA TIMUR",
        "JEMBRANA": "BALI","TABANAN": "BALI","BADUNG": "BALI","GIANYAR": "BALI",
        "KLUNGKUNG": "BALI","BANGLI": "BALI","KARANG ASEM": "BALI","BULELENG": "BALI","DENPASAR": "BALI",
        "LOMBOK BARAT": "NUSA TENGGARA BARAT","LOMBOK TENGAH": "NUSA TENGGARA BARAT",
        "LOMBOK TIMUR": "NUSA TENGGARA BARAT","SUMBAWA": "NUSA TENGGARA BARAT",
        "DOMPU": "NUSA TENGGARA BARAT","BIMA": "NUSA TENGGARA BARAT",
        "SUMBAWA BARAT": "NUSA TENGGARA BARAT","LOMBOK UTARA": "NUSA TENGGARA BARAT",
        "MATARAM": "NUSA TENGGARA BARAT",
        "SUMBA BARAT": "NUSA TENGGARA TIMUR","SUMBA TIMUR": "NUSA TENGGARA TIMUR",
        "KUPANG": "NUSA TENGGARA TIMUR","TIMOR TENGAH SELATAN": "NUSA TENGGARA TIMUR",
        "TIMOR TENGAH UTARA": "NUSA TENGGARA TIMUR","BELU": "NUSA TENGGARA TIMUR",
        "ALOR": "NUSA TENGGARA TIMUR","LEMBATA": "NUSA TENGGARA TIMUR",
        "FLORES TIMUR": "NUSA TENGGARA TIMUR","SIKKA": "NUSA TENGGARA TIMUR",
        "ENDE": "NUSA TENGGARA TIMUR","NGADA": "NUSA TENGGARA TIMUR",
        "MANGGARAI": "NUSA TENGGARA TIMUR","ROTE NDAO": "NUSA TENGGARA TIMUR",
        "MANGGARAI BARAT": "NUSA TENGGARA TIMUR","SUMBA TENGAH": "NUSA TENGGARA TIMUR",
        "SUMBA BARAT DAYA": "NUSA TENGGARA TIMUR","NAGEKEO": "NUSA TENGGARA TIMUR",
        "MANGGARAI TIMUR": "NUSA TENGGARA TIMUR","SABU RAIJUA": "NUSA TENGGARA TIMUR",
        "MALAKA": "NUSA TENGGARA TIMUR",
        "SAMBAS": "KALIMANTAN BARAT","BENGKAYANG": "KALIMANTAN BARAT","LANDAK": "KALIMANTAN BARAT",
        "MEMPAWAH": "KALIMANTAN BARAT","SANGGAU": "KALIMANTAN BARAT","KETAPANG": "KALIMANTAN BARAT",
        "SINTANG": "KALIMANTAN BARAT","KAPUAS HULU": "KALIMANTAN BARAT","SEKADAU": "KALIMANTAN BARAT",
        "MELAWI": "KALIMANTAN BARAT","KAYONG UTARA": "KALIMANTAN BARAT","KUBU RAYA": "KALIMANTAN BARAT",
        "PONTIANAK": "KALIMANTAN BARAT","SINGKAWANG": "KALIMANTAN BARAT",
        "KOTAWARINGIN BARAT": "KALIMANTAN TENGAH","KOTAWARINGIN TIMUR": "KALIMANTAN TENGAH",
        "KAPUAS": "KALIMANTAN TENGAH","BARITO SELATAN": "KALIMANTAN TENGAH",
        "BARITO UTARA": "KALIMANTAN TENGAH","SUKAMARA": "KALIMANTAN TENGAH",
        "LAMANDAU": "KALIMANTAN TENGAH","SERUYAN": "KALIMANTAN TENGAH","KATINGAN": "KALIMANTAN TENGAH",
        "PULANG PISAU": "KALIMANTAN TENGAH","GUNUNG MAS": "KALIMANTAN TENGAH",
        "BARITO TIMUR": "KALIMANTAN TENGAH","MURUNG RAYA": "KALIMANTAN TENGAH",
        "PALANGKA RAYA": "KALIMANTAN TENGAH",
        "TANAH LAUT": "KALIMANTAN SELATAN","KOTA BARU": "KALIMANTAN SELATAN",
        "BARITO KUALA": "KALIMANTAN SELATAN","TAPIN": "KALIMANTAN SELATAN",
        "HULU SUNGAI SELATAN": "KALIMANTAN SELATAN","HULU SUNGAI TENGAH": "KALIMANTAN SELATAN",
        "HULU SUNGAI UTARA": "KALIMANTAN SELATAN","TABALONG": "KALIMANTAN SELATAN",
        "TANAH BUMBU": "KALIMANTAN SELATAN","BALANGAN": "KALIMANTAN SELATAN",
        "BANJARMASIN": "KALIMANTAN SELATAN","BANJAR BARU": "KALIMANTAN SELATAN",
        "PASER": "KALIMANTAN TIMUR","KUTAI BARAT": "KALIMANTAN TIMUR",
        "KUTAI KARTANEGARA": "KALIMANTAN TIMUR","KUTAI TIMUR": "KALIMANTAN TIMUR",
        "BERAU": "KALIMANTAN TIMUR","PENAJAM PASER UTARA": "KALIMANTAN TIMUR",
        "MAHAKAM HULU": "KALIMANTAN TIMUR","BALIKPAPAN": "KALIMANTAN TIMUR",
        "SAMARINDA": "KALIMANTAN TIMUR","BONTANG": "KALIMANTAN TIMUR",
        "MALINAU": "KALIMANTAN UTARA","BULUNGAN": "KALIMANTAN UTARA","TANA TIDUNG": "KALIMANTAN UTARA",
        "NUNUKAN": "KALIMANTAN UTARA","TARAKAN": "KALIMANTAN UTARA",
        "BOLAANG MONGONDOW": "SULAWESI UTARA","MINAHASA": "SULAWESI UTARA",
        "KEPULAUAN SANGIHE": "SULAWESI UTARA","KEPULAUAN TALAUD": "SULAWESI UTARA",
        "MINAHASA SELATAN": "SULAWESI UTARA","MINAHASA UTARA": "SULAWESI UTARA",
        "BOLAANG MONGONDOW UTARA": "SULAWESI UTARA","SIAU TAGULANDANG BIARO": "SULAWESI UTARA",
        "MINAHASA TENGGARA": "SULAWESI UTARA","BOLAANG MONGONDOW SELATAN": "SULAWESI UTARA",
        "BOLAANG MONGONDOW TIMUR": "SULAWESI UTARA","MANADO": "SULAWESI UTARA",
        "BITUNG": "SULAWESI UTARA","TOMOHON": "SULAWESI UTARA","KOTAMOBAGU": "SULAWESI UTARA",
        "BANGGAI KEPULAUAN": "SULAWESI TENGAH","BANGGAI": "SULAWESI TENGAH",
        "MOROWALI": "SULAWESI TENGAH","POSO": "SULAWESI TENGAH","DONGGALA": "SULAWESI TENGAH",
        "TOLI-TOLI": "SULAWESI TENGAH","BUOL": "SULAWESI TENGAH","PARIGI MOUTONG": "SULAWESI TENGAH",
        "TOJO UNA-UNA": "SULAWESI TENGAH","SIGI": "SULAWESI TENGAH","BANGGAI LAUT": "SULAWESI TENGAH",
        "MOROWALI UTARA": "SULAWESI TENGAH","PALU": "SULAWESI TENGAH",
        "KEPULAUAN SELAYAR": "SULAWESI SELATAN","BULUKUMBA": "SULAWESI SELATAN",
        "BANTAENG": "SULAWESI SELATAN","JENEPONTO": "SULAWESI SELATAN","TAKALAR": "SULAWESI SELATAN",
        "GOWA": "SULAWESI SELATAN","SINJAI": "SULAWESI SELATAN","MAROS": "SULAWESI SELATAN",
        "PANGKAJENE DAN KEPULAUAN": "SULAWESI SELATAN","BARRU": "SULAWESI SELATAN",
        "BONE": "SULAWESI SELATAN","SOPPENG": "SULAWESI SELATAN","WAJO": "SULAWESI SELATAN",
        "SIDENRENG RAPPANG": "SULAWESI SELATAN","PINRANG": "SULAWESI SELATAN",
        "ENREKANG": "SULAWESI SELATAN","LUWU": "SULAWESI SELATAN","TANA TORAJA": "SULAWESI SELATAN",
        "LUWU UTARA": "SULAWESI SELATAN","LUWU TIMUR": "SULAWESI SELATAN",
        "TORAJA UTARA": "SULAWESI SELATAN","MAKASSAR": "SULAWESI SELATAN",
        "PAREPARE": "SULAWESI SELATAN","PALOPO": "SULAWESI SELATAN",
        "BUTON": "SULAWESI TENGGARA","MUNA": "SULAWESI TENGGARA","KONAWE": "SULAWESI TENGGARA",
        "KOLAKA": "SULAWESI TENGGARA","KONAWE SELATAN": "SULAWESI TENGGARA",
        "BOMBANA": "SULAWESI TENGGARA","WAKATOBI": "SULAWESI TENGGARA",
        "KOLAKA UTARA": "SULAWESI TENGGARA","BUTON UTARA": "SULAWESI TENGGARA",
        "KONAWE UTARA": "SULAWESI TENGGARA","KOLAKA TIMUR": "SULAWESI TENGGARA",
        "KONAWE KEPULAUAN": "SULAWESI TENGGARA","MUNA BARAT": "SULAWESI TENGGARA",
        "BUTON TENGAH": "SULAWESI TENGGARA","BUTON SELATAN": "SULAWESI TENGGARA",
        "KENDARI": "SULAWESI TENGGARA","BAUBAU": "SULAWESI TENGGARA",
        "BOALEMO": "GORONTALO","GORONTALO": "GORONTALO","POHUWATO": "GORONTALO",
        "BONE BOLANGO": "GORONTALO","GORONTALO UTARA": "GORONTALO",
        "MAJENE": "SULAWESI BARAT","POLEWALI MANDAR": "SULAWESI BARAT","MAMASA": "SULAWESI BARAT",
        "MAMUJU": "SULAWESI BARAT","MAMUJU UTARA": "SULAWESI BARAT","MAMUJU TENGAH": "SULAWESI BARAT",
        "MALUKU TENGGARA BARAT": "MALUKU","MALUKU TENGGARA": "MALUKU","MALUKU TENGAH": "MALUKU",
        "BURU": "MALUKU","KEPULAUAN ARU": "MALUKU","SERAM BAGIAN BARAT": "MALUKU",
        "SERAM BAGIAN TIMUR": "MALUKU","MALUKU BARAT DAYA": "MALUKU","BURU SELATAN": "MALUKU",
        "AMBON": "MALUKU","TUAL": "MALUKU",
        "HALMAHERA BARAT": "MALUKU UTARA","HALMAHERA TENGAH": "MALUKU UTARA",
        "KEPULAUAN SULA": "MALUKU UTARA","HALMAHERA SELATAN": "MALUKU UTARA",
        "HALMAHERA UTARA": "MALUKU UTARA","HALMAHERA TIMUR": "MALUKU UTARA",
        "PULAU MOROTAI": "MALUKU UTARA","PULAU TALIABU": "MALUKU UTARA",
        "TERNATE": "MALUKU UTARA","TIDORE KEPULAUAN": "MALUKU UTARA",
        "FAKFAK": "PAPUA BARAT","KAIMANA": "PAPUA BARAT","TELUK WONDAMA": "PAPUA BARAT",
        "TELUK BINTUNI": "PAPUA BARAT","MANOKWARI": "PAPUA BARAT","SORONG SELATAN": "PAPUA BARAT",
        "SORONG": "PAPUA BARAT","RAJA AMPAT": "PAPUA BARAT","TAMBRAUW": "PAPUA BARAT",
        "MAYBRAT": "PAPUA BARAT","MANOKWARI SELATAN": "PAPUA BARAT","PEGUNUNGAN ARFAK": "PAPUA BARAT",
        "MERAUKE": "PAPUA","JAYAWIJAYA": "PAPUA","JAYAPURA": "PAPUA","NABIRE": "PAPUA",
        "KEPULAUAN YAPEN": "PAPUA","BIAK NUMFOR": "PAPUA","PANIAI": "PAPUA","PUNCAK JAYA": "PAPUA",
        "MIMIKA": "PAPUA","BOVEN DIGOEL": "PAPUA","MAPPI": "PAPUA","ASMAT": "PAPUA",
        "YAHUKIMO": "PAPUA","PEGUNUNGAN BINTANG": "PAPUA","TOLIKARA": "PAPUA","SARMI": "PAPUA",
        "KEEROM": "PAPUA","WAROPEN": "PAPUA","SUPIORI": "PAPUA","MAMBERAMO RAYA": "PAPUA",
        "NDUGA": "PAPUA","LANNY JAYA": "PAPUA","MAMBERAMO TENGAH": "PAPUA","YALIMO": "PAPUA",
        "PUNCAK": "PAPUA","DOGIYAI": "PAPUA","INTAN JAYA": "PAPUA","DEIYAI": "PAPUA",
        # Jakarta as standalone city (maps to DKI JAKARTA province)
        "JAKARTA": "DKI JAKARTA",
        # Tambahan kota-kota umum yang sering muncul di job posting
        "TANGERANG": "BANTEN","TANGERANG SELATAN": "BANTEN","SERANG": "BANTEN","CILEGON": "BANTEN",
        "PANDEGLANG": "BANTEN","LEBAK": "BANTEN",
    }

    PROVINCE_ALIASES = {
        "WEST JAVA": "JAWA BARAT",
        "CENTRAL JAVA": "JAWA TENGAH",
        "EAST JAVA": "JAWA TIMUR",
        "WEST KALIMANTAN": "KALIMANTAN BARAT",
        "CENTRAL KALIMANTAN": "KALIMANTAN TENGAH",
        "SOUTH KALIMANTAN": "KALIMANTAN SELATAN",
        "EAST KALIMANTAN": "KALIMANTAN TIMUR",
        "NORTH KALIMANTAN": "KALIMANTAN UTARA",
        "NORTH SULAWESI": "SULAWESI UTARA",
        "CENTRAL SULAWESI": "SULAWESI TENGAH",
        "SOUTH SULAWESI": "SULAWESI SELATAN",
        "WEST SULAWESI": "SULAWESI BARAT",
        "SOUTHEAST SULAWESI": "SULAWESI TENGGARA",
        "NORTH SUMATRA": "SUMATERA UTARA",
        "WEST SUMATRA": "SUMATERA BARAT",
        "SOUTH SUMATRA": "SUMATERA SELATAN",
        "NORTH MALUKU": "MALUKU UTARA",
        "WEST PAPUA": "PAPUA BARAT",
        "SPECIAL CAPITAL REGION OF JAKARTA": "DKI JAKARTA",
        "DKI": "DKI JAKARTA",
        "SPECIAL REGION OF YOGYAKARTA": "DI YOGYAKARTA",
        "DIY": "DI YOGYAKARTA",
    }

    # English aliases for kabupaten/kota (city/regency level), checked BEFORE
    # the generic substring fallback in find_kabupaten(). Without this,
    # "WEST JAKARTA" would match the standalone "JAKARTA" entry as a whole
    # word inside the string (since "JAKARTA" really is a separate word
    # there), and incorrectly resolve to plain "Jakarta" (province-level)
    # instead of "Jakarta Barat" (city-level). Same risk applies to any other
    # kabupaten/kota whose Indonesian name has an English directional
    # counterpart.
    KABUPATEN_ALIASES = {
        "WEST JAKARTA": "JAKARTA BARAT",
        "EAST JAKARTA": "JAKARTA TIMUR",
        "SOUTH JAKARTA": "JAKARTA SELATAN",
        "NORTH JAKARTA": "JAKARTA UTARA",
        "CENTRAL JAKARTA": "JAKARTA PUSAT",
        "SOUTH TANGERANG": "TANGERANG SELATAN",
        "WEST BANDUNG": "BANDUNG BARAT",
        "WEST LOMBOK": "LOMBOK BARAT",
        "CENTRAL LOMBOK": "LOMBOK TENGAH",
        "EAST LOMBOK": "LOMBOK TIMUR",
        "NORTH LOMBOK": "LOMBOK UTARA",
    }

    KABUPATEN_NAMES: Set[str] = set(KABUPATEN_TO_PROVINSI.keys())
    PROVINCE_NAMES: Set[str] = set(KABUPATEN_TO_PROVINSI.values())

    @classmethod
    def get_province(cls, kabupaten: str) -> Optional[str]:
        return cls.KABUPATEN_TO_PROVINSI.get(kabupaten.upper())

    @classmethod
    def is_kabupaten(cls, name: str) -> bool:
        return name.upper() in cls.KABUPATEN_NAMES

    @classmethod
    def is_province(cls, name: str) -> bool:
        return name.upper() in cls.PROVINCE_NAMES

    @classmethod
    def resolve_province_alias(cls, text: str) -> Optional[str]:
        return cls.PROVINCE_ALIASES.get(text.upper())

    @classmethod
    def resolve_kabupaten_alias(cls, text: str) -> Optional[str]:
        return cls.KABUPATEN_ALIASES.get(text.upper())

    @classmethod
    def find_kabupaten(cls, text: str) -> Optional[str]:
        text_upper = text.upper().strip()

        # Exact match first
        if text_upper in cls.KABUPATEN_NAMES:
            return text_upper

        # Remove prefix then try again
        cleaned = re.sub(r'^(KOTA|KABUPATEN|PROVINSI)\s+', '', text_upper).strip()
        if cleaned in cls.KABUPATEN_NAMES:
            return cleaned

        # English alias check (e.g. "WEST JAKARTA" -> "JAKARTA BARAT").
        # MUST run before the substring fallback below: otherwise a name
        # like "WEST JAKARTA" would match the standalone "JAKARTA" entry as
        # a whole word (since it genuinely appears as a separate word there)
        # and incorrectly resolve to province-level "Jakarta" instead of
        # city-level "Jakarta Barat".
        alias = cls.resolve_kabupaten_alias(text_upper)
        if alias:
            return alias
        alias = cls.resolve_kabupaten_alias(cleaned)
        if alias:
            return alias

        # Word-boundary match: kabupaten name must appear as a WHOLE WORD
        # inside the text, not as a substring of a longer word.
        # (prevents "LANDAK" matching inside "CILANDAK", and similarly
        # prevents "JAKARTA" matching inside "JAKARTA SELATAN" being wrong —
        # that case is fine since JAKARTA SELATAN is its own kabupaten entry
        # and is checked via exact match above first.)
        best = None
        best_len = 0
        for kab in cls.KABUPATEN_NAMES:
            pattern = r'\b' + re.escape(kab) + r'\b'
            if re.search(pattern, text_upper) and len(kab) > best_len:
                best = kab
                best_len = len(kab)
        if best:
            return best

        return None

    @classmethod
    def find_province(cls, text: str) -> Optional[str]:
        text_upper = text.upper().strip()

        # Check English alias first
        alias = cls.resolve_province_alias(text_upper)
        if alias:
            return alias

        # Exact match
        if text_upper in cls.PROVINCE_NAMES:
            return text_upper

        # Word-boundary match (same fix as find_kabupaten, for consistency
        # and to avoid analogous false positives on province names).
        best = None
        best_len = 0
        for prov in cls.PROVINCE_NAMES:
            pattern = r'\b' + re.escape(prov) + r'\b'
            if re.search(pattern, text_upper) and len(prov) > best_len:
                best = prov
                best_len = len(prov)
        return best


class LocationNormalizer:

    NOISE_WORDS = {
        "remote", "online", "hybrid", "work from home", "wfh",
        "freelance", "contract", "part-time", "temporary",
        "onsite", "office", "full-time", "full time", "telecommute"
    }

    @classmethod
    def _remove_noise(cls, location: str) -> str:
        if not location:
            return location
        location = re.sub(r'\s*\(\d+\)\s*', ' ', location)
        for noise in cls.NOISE_WORDS:
            location = re.sub(r'\b' + re.escape(noise) + r'\b', '', location, flags=re.IGNORECASE)
        location = re.sub(r'\s+', ' ', location).strip()
        location = re.sub(r'^[,\s]+|[,\s]+$', '', location).strip()
        return location

    @classmethod
    def _split_parts(cls, location: str) -> List[str]:
        """Split location by comma or slash, return all non-empty parts"""
        parts = re.split(r'[,/]', location)
        return [p.strip() for p in parts if p.strip()]

    @classmethod
    def _clean_prefixes(cls, name: str) -> str:
        name = re.sub(r'^(KOTA|KABUPATEN|PROVINSI|DAERAH ISTIMEWA|DAERAH|ISTIMEWA)\s+', '', name.upper()).strip()
        return name

    @classmethod
    def normalize(cls, location: Optional[str]) -> str:
        if not location:
            return "other"

        # Step 1: remove noise
        cleaned = cls._remove_noise(location)
        if not cleaned:
            return "other"

        # Step 2: split into parts (e.g. "Jakarta, Indonesia" → ["Jakarta", "Indonesia"])
        parts = cls._split_parts(cleaned)
        if not parts:
            return "other"

        # Step 3: try each part (most specific first = first part)
        for part in parts:
            upper = part.upper()

            # Skip "INDONESIA" word at part level — it's a country fallback, not a city
            if upper == "INDONESIA":
                continue

            # Try to find kabupaten in this part
            kab = KabupatenData.find_kabupaten(cls._clean_prefixes(part))
            if kab:
                return kab.title()

            # Try province
            prov = KabupatenData.find_province(cls._clean_prefixes(part))
            if prov:
                return prov.title()

        # Step 4: if ALL parts are only "Indonesia" → return Indonesia
        all_indonesia = all(p.upper() == "INDONESIA" for p in parts)
        if all_indonesia or any(p.upper() == "INDONESIA" for p in parts):
            # Only return Indonesia if no city/province was found above
            return "Indonesia"

        # Step 5: fallback — return first meaningful part as-is
        return parts[0].title() if parts else "other"

    @classmethod
    def normalize_with_type(cls, location: Optional[str]) -> LocationResult:
        normalized = cls.normalize(location)
        norm_upper = normalized.upper()

        if normalized == "other":
            location_type = LocationType.OTHER
        elif normalized == "Indonesia":
            location_type = LocationType.INDONESIA
        elif KabupatenData.is_province(norm_upper):
            location_type = LocationType.PROVINCE
        elif KabupatenData.is_kabupaten(norm_upper):
            location_type = LocationType.CITY
        else:
            location_type = LocationType.OTHER

        return LocationResult(
            normalized=normalized,
            original=location or "",
            location_type=location_type,
            confidence=1.0 if normalized not in ["other", "Indonesia"] else 0.5
        )

    @classmethod
    def normalize_batch(cls, locations: List[str]) -> List[str]:
        return [cls.normalize(loc) for loc in locations]

    @classmethod
    def get_statistics(cls, locations: List[str]) -> Dict[str, int]:
        stats = {}
        for loc in locations:
            if not loc:
                continue
            normalized = cls.normalize(loc)
            if normalized:
                stats[normalized] = stats.get(normalized, 0) + 1
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

    @classmethod
    def get_province(cls, location: str) -> Optional[str]:
        normalized = cls.normalize(location)
        if KabupatenData.is_kabupaten(normalized.upper()):
            return KabupatenData.get_province(normalized.upper())
        return None


if __name__ == "__main__":
    test_locations = [
        ("Jakarta", "Jakarta"),
        ("Jakarta Selatan", "Jakarta Selatan"),
        ("DKI Jakarta", "Jakarta"),  # DKI JAKARTA contains JAKARTA kabupaten entry
        ("Jakarta, Indonesia", "Jakarta"),
        ("Jakarta Selatan, DKI Jakarta", "Jakarta Selatan"),
        ("Jakarta Utara", "Jakarta Utara"),
        ("Bandung", "Bandung"),
        ("Kota Bandung", "Bandung"),
        ("Bandung, West Java", "Bandung"),
        ("Kabupaten Bandung", "Bandung"),
        ("Yogyakarta", "Yogyakarta"),
        ("Surabaya", "Surabaya"),
        ("Tangerang", "Tangerang"),
        ("Bekasi", "Bekasi"),
        ("Depok", "Depok"),
        ("Bogor", "Bogor"),
        ("West Java", "Jawa Barat"),
        ("Central Java", "Jawa Tengah"),
        ("East Java", "Jawa Timur"),
        ("Bali", "Bali"),
        ("Aceh", "Aceh"),
        ("Indonesia", "Indonesia"),
        ("Remote, Indonesia", "Indonesia"),
        ("Remote", "other"),
        ("WFH", "other"),
        ("Jakarta (415)", "Jakarta"),
        ("Jakarta, Remote", "Jakarta"),
        ("Bandung, WFH", "Bandung"),
        ("Singapore", "Singapore"),
        ("Tokyo", "Tokyo"),
        ("", "other"),
        (None, "other"),
        # --- Regression tests for the "Cilandak -> Landak" substring bug ---
        # "Cilandak" is a kecamatan (sub-district), not a kabupaten/kota, so it
        # doesn't match on its own and normalize() falls through to the next
        # part ("Jakarta"/"Jakarta Selatan"). The bug was that it used to
        # falsely match "Landak" (a real kabupaten in Kalimantan Barat) via
        # unguarded substring search. The fix below just stops that false
        # match — it does NOT make "Cilandak" resolve to itself, since it's
        # not in KABUPATEN_TO_PROVINSI at all.
        ("Cilandak, Jakarta, Indonesia", "Jakarta"),
        ("Cilandak, Jakarta Selatan", "Jakarta Selatan"),
        ("Cilandak", "Cilandak"),  # no other part to fall back to -> Step 5 fallback, as-is
        ("Cimahi", "Cimahi"),
        ("Cirebon", "Cirebon"),
        # --- Regression tests for the "West Jakarta -> Jakarta" alias bug ---
        # Previously "WEST JAKARTA" matched the standalone "JAKARTA" entry
        # as a whole word (word-boundary substring match still matched it,
        # since JAKARTA really is a separate word inside "WEST JAKARTA"),
        # so it wrongly resolved to province-level "Jakarta" instead of
        # city-level "Jakarta Barat". The fix adds explicit English aliases
        # for these directional city names, checked before the substring
        # fallback.
        ("West Jakarta", "Jakarta Barat"),
        ("East Jakarta", "Jakarta Timur"),
        ("South Jakarta", "Jakarta Selatan"),
        ("North Jakarta", "Jakarta Utara"),
        ("Central Jakarta", "Jakarta Pusat"),
        ("West Jakarta, Jakarta, Indonesia", "Jakarta Barat"),
        ("Malang, East Java, Indonesia", "Malang"),
        ("Purbalingga, Central Java, Indonesia", "Purbalingga"),
        ("South Tangerang", "Tangerang Selatan"),
        ("West Bandung", "Bandung Barat"),
    ]

    print("=" * 75)
    print("LOCATION NORMALIZATION TEST")
    print("=" * 75)
    print(f"{'Input':<35} {'Expected':<25} {'Got':<25} {'Status'}")
    print("-" * 75)

    passed = 0
    failed = 0

    for location, expected in test_locations:
        result = LocationNormalizer.normalize(location)
        ok = result == expected
        status = "✅" if ok else "❌"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"{str(location):<35} {expected:<25} {result:<25} {status}")

    print("=" * 75)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_locations)} tests")
    print("=" * 75)
    print(f"\nTotal kabupaten/kota: {len(KabupatenData.KABUPATEN_NAMES)}")
    print(f"Total provinsi      : {len(KabupatenData.PROVINCE_NAMES)}")