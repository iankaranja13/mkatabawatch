# Tanzania NeST Open Contracting Data Portal — Data Source Notes

**Project:** MkatabaWatch — Public Contracts, Public Evidence  
**Investigated Portal:** [https://data.nest.go.tz](https://data.nest.go.tz)  
**Publisher:** Public Procurement Regulatory Authority (PPRA), United Republic of Tanzania  
**Standard:** Open Contracting Data Standard (OCDS) v1.1  
**Investigation Date:** September 2026  

---

## 1. Official Architecture & Endpoints

The Tanzania PPRA NeST Data Portal is built as an Angular application interacting with an API gateway backend (`https://nest.go.tz/gateway/nest-data-portal-api/`).

### A. Live OCDS REST API Endpoints (No Authentication Required)

| Endpoint | Method | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `https://nest.go.tz/gateway/nest-data-portal-api/api/releases` | `GET` | `cursor` (int, default 0), `since` (ISO 8601, e.g. `2024-06-01T00:00:00Z`), `ocid` | Retrieves paginated OCDS Release Packages (50 releases per page) with cursor-based pagination via `links.next`. |
| `https://nest.go.tz/gateway/nest-data-portal-api/api/releases/{ocid}/{releaseId}` | `GET` | `ocid`, `releaseId` | Fetch a specific single release. |
| `https://nest.go.tz/gateway/nest-data-portal-api/api/records/{ocid}` | `GET` | `ocid` | Fetch the complete compiled OCDS record for any OCID, including tender description, buyer, procuring entity, award amounts, supplier details, and contract periods. |

### B. Bulk Download Packages

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST https://nest.go.tz/gateway/nest-data-portal-api/packages` | `POST` | Lists all 2,450+ bulk daily and monthly packages. |
| `GET https://nest.go.tz/gateway/nest-data-portal-api/api/packages/download/{fileName}` | `GET` | Direct download of bulk OCDS packages in JSON (`.json`) or Excel (`.xlsx`) format (e.g. `record_2024_06.json`). |
| `GET https://nest.go.tz/gateway/nest-data-portal-api/api/packages/download-zip` | `GET` | Zip package download filtered by date range and frequency. |

---

## 2. Available Formats

1. **OCDS Standard JSON (v1.1):** Available both live via REST endpoints and via bulk downloads.
2. **Microsoft Excel (XLSX):** Available via bulk download packages.
3. **Zip Archives:** Available for batch downloads.

---

## 3. Fields Populated in Practice

Our programmatic inspection of live releases and compiled records reveals the following field population:

| OCDS Field | Populated in Practice? | Notes |
| :--- | :---: | :--- |
| **OCID** | ✅ Yes | Format: `ocds-mv5oob-{EntityCode}-{Year}-{Category}-{Number}` |
| **Buyer / Entity Name** | ✅ Yes | Populated across ministries, city councils, agencies (e.g., *National Irrigation Commission*, *Dar es Salaam City Council*, *Ministry of Health*) |
| **Buyer Region & Location** | ✅ Yes | Available in `compiledRelease.parties` (e.g., *Dodoma*, *Arusha*, *Dar es Salaam*, *Mwanza*, *Tanga*) |
| **Project Title / Description** | ✅ Yes | Clear descriptions in `tender.description` and `contracts.description` |
| **Contract Value & Currency** | ✅ Yes | Accurate amounts in Tanzanian Shillings (`TZS`), e.g., TZS 20,763,431,410.00 |
| **Contractor / Supplier Name** | ✅ Yes | Real registered vendor names in `awards.suppliers` (e.g. *CRJE (East Africa) Limited*, *China Railway 15*, *Crossworld Construction*) |
| **Award Date** | ✅ Yes | ISO 8601 timestamp in `awards[].date` |
| **Contract Period & Duration** | ✅ Yes | Start date, end date, and `durationInDays` in `contracts[].period` |
| **Status / Progress** | ⚠️ Partial | `tender.status` (e.g., `complete`), `contracts.status` (e.g., `pending`, `active`). Specific milestone % progress is rarely populated in raw OCDS feeds, making community monitoring particularly vital. |

---

## 4. Real Data Volume & Coverage

* **Time Horizon:** Data spans from late 2022 through 2023/2024 and 2024/2025 financial years.
* **Volume:** 2,450+ bulk packages, tens of thousands of individual procurement releases nationwide.
* **Geographical Coverage:** All 31 regions of Tanzania (Mainland & Zanzibar), covering national ministries, executive agencies (TARURA, TANESCO, NIRC), regional secretariats, and local government authorities (LGAs).
* **Sectors Represented:**
  - Water & Irrigation (Dams, irrigation schemes, treatment plants)
  - Transport Infrastructure (Bridges, box culverts, roads, administrative headquarters)
  - Education (Secondary school classrooms, primary dormitories, administration blocks)
  - Healthcare (Hospital construction supervision, health training centre remodeling, dispensary fitouts)

---

## 5. Selected 10 Real Projects for MkatabaWatch Demo

The following 10 projects were extracted directly from `https://nest.go.tz/gateway/nest-data-portal-api/api/records/{ocid}` and saved to `data/verified_sample_projects.json`. They provide high-visibility, diverse public works across Tanzania for our community evidence loop:

### 1. Luiche Dam Construction (Kigoma)
* **OCID:** `ocds-mv5oob-00005-2023-2024-W-78-S001`
* **Title:** Construction of Luiche Dam at Kigoma District in Kigoma Region
* **Procuring Entity:** National Irrigation Commission
* **Contractor:** CRJE (East Africa) Limited
* **Contract Value:** **TZS 20,763,431,410.00** (~$7.8M USD)
* **Location:** Kigoma District, Kigoma Region
* **Sector:** Water & Strategic Infrastructure

### 2. Mgambalenga Irrigation Scheme (Iringa)
* **OCID:** `ocds-mv5oob-00005-2023-2024-W-71-S001`
* **Title:** Construction of Mgambalenga Irrigation Scheme at Kilolo District in Iringa Region
* **Procuring Entity:** National Irrigation Commission
* **Contractor:** China Railway 15 Bureau Group Corporation
* **Contract Value:** **TZS 20,282,721,515.00** (~$7.6M USD)
* **Location:** Kilolo District, Iringa Region
* **Sector:** Agriculture & Water

### 3. Chinangali Irrigation Scheme & Boreholes (Dodoma)
* **OCID:** `ocds-mv5oob-00005-2023-2024-W-128-S001`
* **Title:** Construction, Installation of Irrigation Systems and Borehole Drilling for Chinangali Irrigation Scheme at Chamwino District
* **Procuring Entity:** National Irrigation Commission
* **Contractor:** STC Construction Company Limited
* **Contract Value:** **TZS 16,303,775,772.00** (~$6.1M USD)
* **Location:** Chamwino District, Dodoma Region
* **Sector:** Water & Drilling

### 4. Dar es Salaam Box Culverts & Drainage Bridges (Dar es Salaam)
* **OCID:** `ocds-mv5oob-88Z1-2023-2024-W-82-S001`
* **Title:** Construction of Box Culvert at Msumi-Bombambili, Kavesu-Liwiti and Kwa Mzava and Drift at Kisukuru
* **Procuring Entity:** Dar es Salaam City Council
* **Contractor:** Crossworld Construction Company Limited
* **Contract Value:** **TZS 1,522,225,450.00** (~$570,000 USD)
* **Location:** Msumi / Kisukuru, Dar es Salaam City
* **Sector:** Urban Roads & Flood Mitigation

### 5. Ukerewe Referral Hospital Construction Supervision (Mwanza)
* **OCID:** `ocds-mv5oob-81-2023-2024-C-01-S002`
* **Title:** Consultancy Services for Conceptual Design, Detailed Design and Construction Supervision of Proposed Referral Hospital (Ukerewe District)
* **Procuring Entity:** Mwanza Regional Secretariat
* **Contractor:** Malk Consultants Limited
* **Contract Value:** **TZS 960,745,000.00** (~$360,000 USD)
* **Period:** 2024-06-10 to 2027-06-10 (1,095 Days)
* **Location:** Ukerewe District, Mwanza Region (Lake Victoria Island)
* **Sector:** Healthcare Infrastructure

### 6. Korogwe Water Treatment Plant (Tanga)
* **OCID:** `ocds-mv5oob-TR163-2023-2024-W-03-S003`
* **Title:** Construction of Korogwe Treatment Plant
* **Procuring Entity:** Handeni Trunk Main Water Supply and Sanitation Authority
* **Contractor:** Tumaini Civil Works Limited
* **Contract Value:** **TZS 888,169,360.00** (~$335,000 USD)
* **Period:** 2024-07-23 to 2025-07-23 (365 Days)
* **Location:** Korogwe, Tanga Region
* **Sector:** Clean Water & Sanitation

### 7. TARURA National Headquarters Supervision (Dodoma)
* **OCID:** `ocds-mv5oob-S10-2023-2024-C-14-S001`
* **Title:** Consultancy Service for Supervision of the Construction of TARURA HQ Building at Njedengwa Investment Area
* **Procuring Entity:** Tanzania Rural and Urban Roads Agency (TARURA)
* **Contractor:** National Housing Corporation (NHC)
* **Contract Value:** **TZS 560,451,500.00** (~$210,000 USD)
* **Period:** 2024-06-24 to 2025-07-21 (392 Days)
* **Location:** Njedengwa, Dodoma Capital City
* **Sector:** Public Administration & Buildings

### 8. CEDHA Health Training Centre Remodeling (Arusha)
* **OCID:** `ocds-mv5oob-52-2023-2024-C-21-S001`
* **Title:** Provision of Consultancy Service for Proposed Remodeling of Centre for Educational Development in Health, Arusha (CEDHA) at Sanawari
* **Procuring Entity:** Ministry of Health
* **Contractor:** Digital Space Consultancy Limited
* **Contract Value:** **TZS 261,764,000.00** (~$98,000 USD)
* **Period:** 2024-06-10 to 2025-06-10 (365 Days)
* **Location:** Sanawari, Arusha Municipality
* **Sector:** Healthcare Education

### 9. Namanga Border Rest House Construction (Arusha / Kenya Border)
* **OCID:** `ocds-mv5oob-X2-2023-2024-W-09-S001`
* **Title:** Proposed Construction of Rest House Building at Namanga Border in Longido District
* **Procuring Entity:** Government Chemist Laboratory Authority
* **Contractor:** Swash Construction Co. Limited
* **Contract Value:** **TZS 174,573,000.00** (~$65,000 USD)
* **Period:** 2024-06-14 to 2024-12-11 (180 Days)
* **Location:** Namanga Border, Longido District, Arusha Region
* **Sector:** Border Facilities & Government Services

### 10. Mtimbira Primary School Dormitory for 80 Pupils (Morogoro)
* **OCID:** `ocds-mv5oob-79K7-2023-2024-G-566-S001`
* **Title:** Building Materials for Construction of a Dormitory for 80 Pupils at Mtimbira Primary School
* **Procuring Entity:** Malinyi District Council
* **Contractor:** Zidadu General Supplies
* **Contract Value:** **TZS 82,195,600.00** (~$31,000 USD)
* **Period:** 2024-05-27 to 2024-06-26 (30 Days)
* **Location:** Mtimbira, Malinyi District, Morogoro Region
* **Sector:** Primary Education & Child Welfare

---

## 6. Authentication & Rate Limits
* **API Key:** None required. Endpoints respond openly to HTTP requests with appropriate headers.
* **Rate Limits:** Standard web server throttle; we observed zero 429 rate limit responses during 50-item batched requests.
* **Caching Strategy:** MkatabaWatch caches ingested OCDS JSON releases locally in SQLite/JSON to prevent unnecessary load on public infrastructure and provide instant sub-millisecond response times for users.
