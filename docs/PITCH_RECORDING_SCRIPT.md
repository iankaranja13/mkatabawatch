# 🎬 MkatabaWatch Pitch Video: Recording Guide & Script

**Target Duration:** ~3 Minutes 30 Seconds (Optimal for Hackathon Judges)  
**Deliverable:** Screen Recording + Voiceover (or webcam inset)  
**Tools Recommended:** Loom, OBS Studio, or Mac QuickTime Screen Recording (`Cmd + Shift + 5`)

---

## 🛠️ Pre-Recording Checklist (2 Minutes Before Recording)

1. **Terminal:** Make sure the backend server is running:
   ```bash
   ./run.sh
   # Confirmed running at http://localhost:8001
   ```
2. **Browser Tab 1 (Live App):** Open `http://localhost:8001` in Google Chrome or Brave.
   - Set zoom level to `100%` or `110%` for crisp text readability.
   - Start on **Screen 1 (Project Explorer)**.
   - Ensure Language is set to **English** (you will toggle Swahili during the demo).
3. **Browser Tab 2 / PDF Viewer (Pitch Deck):** Open `MkatabaWatch_Pitch_Deck.pdf` in full-screen presentation mode (`Cmd + Ctrl + F` in Preview, or fullscreen in Chrome).
4. **Window Arrangement:** Have both windows ready to switch via `Cmd + Tab`.
5. **Microphone:** Test audio levels; ensure clear vocal pickup with minimal background noise.

---

## ⏱️ Video Structure Overview

| Segment | Timing | Visual Focus | Core Message |
|---|---|---|---|
| **1. Hook & The Problem** | 0:00 – 0:45 (45s) | Slides 1 & 2 | The physical blindspot between government procurement portals and ground reality. |
| **2. The Solution Concept** | 0:45 – 1:15 (30s) | Slide 4 | The 4-stage loop: OCDS Ingestion → Community Evidence → Safe AI → Human Verification. |
| **3. LIVE DEMO (The Core)** | 1:15 – 2:30 (75s) | Live Web App (`localhost:8001`) | 10 real NeST projects, instant OCDS inspector, citizen reporting, and safe AI reconciliation. |
| **4. Impact & Technical Edge** | 2:30 – 3:10 (40s) | Slides 6 & 7 | <60KB payload for 3G, reducing audit cycle from 3 years to weeks, pan-African scale. |
| **5. Closing & Vision** | 3:10 – 3:30 (20s) | Slide 8 | "The public pays for the contract. The public should see the evidence." |

---

## 🎙️ Step-by-Step Recording Script

---

### SEGMENT 1: The Problem (0:00 – 0:45)

#### 🖥️ What to Show:
- **0:00 – 0:10:** Full Screen on **Slide 1 (Cover Slide)**.
- **0:10 – 0:45:** Transition smoothly to **Slide 2 (The Problem)**.

#### 🎬 What to Do:
- Start with confident, clear pacing. Move your cursor gently to emphasize the headline points on Slide 2.

#### 🗣️ What to Say:
> *"Hello judges. My name is Ian Karanja, and this is **MkatabaWatch**—a civic accountability platform that bridges the gap between official public contracts and on-the-ground reality in Tanzania.*
>
> *(Switch to Slide 2)*
>
> *Over the past several years, Tanzania's Public Procurement Regulatory Authority has done commendable work by publishing procurement data on the national NeST portal.*
>
> *However, there is a fundamental physical blindspot:*
> *Government portals confirm when a contract is awarded and when money is disbursed, but they cannot verify if concrete was poured, if pipes were buried, or if a classroom was roofed.*
>
> *Citizens walk past abandoned trenches and stalled clinics every day, but without access to the actual contract facts, their complaints are dismissed as unverified noise. Meanwhile, formal audits by the Controller and Auditor General only arrive two to three years later—long after funds are spent and contractors have demobilized.*
>
> *MkatabaWatch solves this."*

---

### SEGMENT 2: The Solution (0:45 – 1:15)

#### 🖥️ What to Show:
- Transition to **Slide 4 (The Solution: 4-Stage Verification Loop)**.

#### 🎬 What to Do:
- Hover your mouse over the 4 numbered quadrants as you speak to guide the viewer’s eyes.

#### 🗣️ What to Say:
> *"MkatabaWatch creates a continuous civic verification loop in four stages:*
>
> *First, we ingest 100% genuine Open Contracting Data Standard records directly from the Tanzania PPRA NeST portal.*
>
> *Second, local community monitors capture lightweight, geotagged photographic evidence on their mobile phones.*
>
> *Third, our responsible AI reconciliation engine compares the contractual timeline and milestone claims against what is physically visible—operating under strict, non-accusatory safety guardrails.*
>
> *And fourth, flagged discrepancies flow into a human verification queue for auditors and civil society investigators to review.*
>
> *Let's see this running live right now."*

---

### SEGMENT 3: Live Application Walkthrough (1:15 – 2:30)

#### 🖥️ What to Show:
- Switch window to the **Live Browser Tab (`http://localhost:8001`)**.

#### 🎬 What to Do & Say (Choreographed):

#### Step 3A: Explorer & Real NeST Data (1:15 – 1:35)
* **Action:** Start on the Home / Projects Explorer screen. Scroll through the project cards.
* **Action:** Click the **Language Toggle** in the top right (`EN / SW`) to demonstrate instant Swahili localization, then switch back to English.
* **Action:** Click on the **"Dar es Salaam Culverts & Bridges"** project card.
* **Speech:**
  > *"Here is the live MkatabaWatch platform. Every project listed here is a real, live Tanzanian contract ingested from the NeST portal—spanning roads, schools, health facilities, and water infrastructure.*
  >
  > *The entire interface is bilingual, allowing citizens to toggle seamlessly between English and Kiswahili.*
  >
  > *Let's look into the Dar es Salaam City Council drainage culvert project, valued at 1.52 Billion Tanzanian Shillings."*

#### Step 3B: Project Detail & Instant OCDS Inspector (1:35 – 1:55)
* **Action:** On the Project Detail view, show the official buyer, supplier, award date, and contract value.
* **Action:** Click the button **"Inspect Raw OCDS JSON"**. The modal pops up instantly. Scroll through the genuine OCDS schema, then close the modal.
* **Speech:**
  > *"On this detail page, citizens see exact contract terms: the buyer, the contractor, and the completion deadline.*
  >
  > *If an investigator wants to verify the provenance, they can click 'Inspect Raw OCDS JSON'. We serve the full, genuine OCDS schema directly from our cache in sub-milliseconds, bypassing slow external government portal routing while maintaining 100% evidentiary fidelity."*

#### Step 3C: AI Reconciliation Engine (1:55 – 2:15)
* **Action:** Click **"AI Reconciliation"** in the top navigation or on the project.
* **Action:** Click the **"Run AI Reconciliation"** button. Watch the reconciliation card appear.
* **Action:** Point out:
  1. The **Status Badge** (`DISCREPANCY FLAGGED` in red/amber).
  2. The side-by-side comparison: Stated Contractual Claim vs. Observed Evidence.
  3. The objective summary and actionable recommendation.
* **Speech:**
  > *"Now, let's trigger the AI Reconciliation Engine.*
  >
  > *The AI performs an objective audit comparison: On one side, the contract states four box culverts were due for completion. On the other side, verified ground photos show an abandoned excavator, flooded trenches, and uninstalled pipes.*
  >
  > *Notice the tone: The AI never hallucinates numbers and never makes illegal accusations of corruption. Instead, it surfaces factual timeline divergence, calculates a confidence score, and recommends targeted engineering inspection."*

#### Step 3D: Community Submission & Human Queue (2:15 – 2:30)
* **Action:** Click **"Submit Evidence"** to show the strict validation form (photo upload, GPS, observation type).
* **Action:** Click **"Verification Queue"** to show the auditor portal where findings can be marked as *Verified*, *Resolved*, or *Dismissed*.
* **Speech:**
  > *"Citizens can submit evidence directly with photos and GPS coordinates through an ultra-lightweight form, and every flagged case enters this Human Verification Queue—keeping civil society auditors firmly in control."*

---

### SEGMENT 4: Impact & Technical Excellence (2:30 – 3:10)

#### 🖥️ What to Show:
- Switch back to the Pitch Deck: **Slide 6 (Technical Architecture)**, then transition to **Slide 7 (Potential Impact)**.

#### 🎬 What to Do:
- Highlight the metric cards on Slide 6 (60 KB payload, OCDS standard compliance), then move to the four impact pillars on Slide 7.

#### 🗣️ What to Say:
> *(Slide 6)*
> *"Under the hood, MkatabaWatch is engineered specifically for African infrastructure reality:*
> *Our entire frontend bundle is under 60 kilobytes. It loads instantly on rural 2G and 3G mobile devices with zero heavy framework bloat.*
>
> *(Switch to Slide 7)*
> *The impact here is transformative:*
>
> *First, it compresses the audit discovery cycle from two to three years down to days or weeks—enabling regional commissioners and procuring entities to intervene before contractors abandon the site.*
>
> *Second, it protects billions in public treasury by enabling authorities to freeze milestone disbursements when physical delivery is absent.*
>
> *And third, because MkatabaWatch is built on the international Open Contracting Data Standard, this architecture can scale across Kenya, Uganda, Ghana, Nigeria, and Rwanda with zero changes to data schema."*

---

### SEGMENT 5: Conclusion & Call to Action (3:10 – 3:30)

#### 🖥️ What to Show:
- Transition to **Slide 8 (Roadmap & Hackathon Vision)**.

#### 🗣️ What to Say:
> *"Today, MkatabaWatch is a fully functioning proof-of-concept tested on over 61 Billion Tanzanian Shillings in live contracts.*
>
> *Our roadmap expands to WhatsApp and Telegram bot reporting, automated EXIF timestamp verification, and direct integration with civil society watchdog networks like WAJIBU and Twaweza.*
>
> *Because at the end of the day, our philosophy is simple:*
> ***The public pays for the contract. The public should see the evidence.***
>
> *Thank you very much."*

---

## 💡 Pro Tips for a Flawless Recording

1. **Practice the Window Switch (`Cmd + Tab`):** Rehearse switching between your browser with `localhost:8001` and your PDF reader twice before hitting record so transitions look instant and smooth.
2. **Cursor Control:** Avoid fast, erratic cursor movements. Move your mouse intentionally to the button or card you are speaking about.
3. **Pacing:** Speak at a steady, measured pace. Take a brief breath between slides.
4. **If you make a mistake:** Don't stop the whole recording! Pause for 2 seconds in silence, re-read the sentence cleanly, and you can trim it in 10 seconds using any free video trimmer or QuickTime.
