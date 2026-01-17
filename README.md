# The Headache Vault - Demo Application

**Demo Date:** February 9, 2026  
**Audience:** Headache Specialists  
**Status:** Week 1 Prototype - Core Search Functionality

## 🎯 Features Implemented

### ✅ Week 1 (Jan 16-23) - CURRENT
- ✅ Search interface with state/payer/drug filters
- ✅ Database A + B + C integration (717 payers, 752 policies, 35 denial codes)
- ✅ Episodic vs Chronic vs Cluster headache type filtering
- ✅ Step therapy requirements display
- ✅ Gold Card status indicators
- ✅ Clinical appeal language lookup
- ✅ Pediatric override checking (Database E)
- ✅ ICD-10 code reference (Master ICD-10)
- ✅ MOH risk screening tool (Master OTC Medications)
- ✅ PA documentation generator

### 🔄 Week 2 (Jan 24-31) - PLANNED
- [ ] Enhanced PA text generation with evidence citations
- [ ] Therapeutic dose threshold validation (Master Therapeutic Doses)
- [ ] State regulatory framework integration (Database F)
- [ ] Copy-to-clipboard functionality
- [ ] Mobile responsive improvements

### 🚀 Week 3 (Feb 1-7) - DEPLOYMENT
- [ ] Deploy to Streamlit Cloud
- [ ] Share headachevault.streamlit.app URL for testing
- [ ] Bug fixes based on feedback
- [ ] UI polish and performance optimization

---

## 🖥️ Local Testing (RIGHT NOW)

### Option 1: Test in Claude's Environment

I can run the app right now in this environment for you to test!

```bash
streamlit run headache_vault_demo.py
```

### Option 2: Run on Your Computer

1. **Install Python** (if not already installed)
   - Download from python.org
   - Version 3.8 or higher

2. **Create project folder**
   ```bash
   mkdir headache_vault_demo
   cd headache_vault_demo
   ```

3. **Copy files** (download from this chat):
   - `headache_vault_demo.py`
   - `requirements.txt`
   - All 8 CSV files

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the app**
   ```bash
   streamlit run headache_vault_demo.py
   ```

6. **Open browser**
   - App will open automatically at `http://localhost:8501`
   - If not, manually navigate to that URL

---

## ☁️ Streamlit Cloud Deployment (Week 3)

### Step 1: Create GitHub Repository

1. Go to github.com and sign in (or create free account)
2. Click "New Repository"
3. Name it: `headache-vault-demo`
4. Select "Public"
5. Click "Create repository"

### Step 2: Upload Files to GitHub

**Option A - GitHub Web Interface (Easiest):**
1. Click "uploading an existing file"
2. Drag and drop:
   - `headache_vault_demo.py`
   - `requirements.txt`
   - All 8 CSV files (Database_A, Database_B, etc.)
3. Click "Commit changes"

**Option B - Command Line:**
```bash
cd headache_vault_demo
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/headache-vault-demo.git
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud

1. Go to share.streamlit.io
2. Sign in with GitHub account
3. Click "New app"
4. Select:
   - **Repository:** `YOUR_USERNAME/headache-vault-demo`
   - **Branch:** `main`
   - **Main file path:** `headache_vault_demo.py`
5. Click "Deploy!"

**Your app will be live at:**
`https://YOUR_USERNAME-headache-vault-demo.streamlit.app`

### Step 4: Custom Domain (Optional - After Demo)

1. Buy domain: `headachevault.com` (~$12/year at Namecheap/GoDaddy)
2. In Streamlit Cloud settings, click "Domains"
3. Add custom domain
4. Update DNS records (Streamlit provides instructions)

---

## 📊 Database Files Required

Make sure these 8 CSV files are in the same directory as the app:

1. `Database_A_FINAL_WITH_LOB_CODE.csv` (1,088 payers)
2. `Database_B_CLUSTER_UPDATED.csv` (752 policies)
3. `Database_C_CLUSTER_UPDATED.csv` (35 denial codes)
4. `Database_E_Pediatric_Overrides.csv` (23 overrides)
5. `Database_F_State_Regulatory_Framework.csv` (50 states)
6. `Master_ICD10_CLUSTER_UPDATED.csv` (46 diagnosis codes)
7. `Master_Therapeutic_Doses_CLUSTER_UPDATED.csv` (40 medications)
8. `Master_OTC_Medications.csv` (28 OTC meds)

---

## 🎨 Demo Day Checklist (February 9)

### February 8 (Day Before)
- [ ] Wake up app at headachevault.streamlit.app (if it went to sleep)
- [ ] Test from conference hotel WiFi
- [ ] Verify all search combinations work
- [ ] Check mobile display on tablet
- [ ] Prepare backup screenshots (in case internet fails)

### February 9 (Demo Day)
- [ ] Open app URL in morning to ensure it's awake
- [ ] Have backup plan ready (local laptop version)
- [ ] Demonstrate key workflows:
  - Search for CGRP mAbs in Pennsylvania
  - Show step therapy requirements
  - Generate PA text
  - Check MOH risk
  - Display ICD-10 codes

---

## 🐛 Troubleshooting

### App won't start locally
- Check Python version: `python --version` (need 3.8+)
- Reinstall dependencies: `pip install -r requirements.txt`
- Verify CSV files are in same directory

### App sleeping on Streamlit Cloud
- Free tier sleeps after 7 days of inactivity
- Solution: Just visit the URL to wake it up (takes ~30 seconds)
- Or upgrade to $20/month for always-on hosting

### CSV files not found
- Make sure all 8 CSV files are uploaded to GitHub
- Check file paths in code match exact filenames
- Files should be in root directory (same folder as .py file)

### Changes not appearing
- Streamlit Cloud auto-deploys when you push to GitHub
- Wait 2-5 minutes for deployment
- Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

---

## 💡 Post-Demo Enhancements

After February 9, if specialists love it:

### Immediate (Week 4-5)
- [ ] Upgrade to Streamlit Pro ($20/month) - removes sleep mode
- [ ] Add user analytics (Google Analytics)
- [ ] Collect specialist feedback
- [ ] Add "Report Issue" button

### Short-term (Month 2-3)
- [ ] Custom domain: headachevault.com
- [ ] Add user authentication
- [ ] Save/export search results
- [ ] Email PA documentation feature

### Long-term (Month 4-6)
- [ ] Rebuild in React/Next.js for production
- [ ] Notion API integration (live data sync)
- [ ] Mobile app version (iOS/Android)
- [ ] Provider portal with case tracking

---

## 📧 Support

Questions during development? Ask in our chat!

**Built with:** Streamlit + Pandas  
**Data Sources:** 8 Notion databases (2,070 total records)  
**Evidence Base:** AHS 2021/2024, ACP 2025, ICHD-3  
**License:** Internal demo - not for public distribution

---

## 🎉 Timeline Status

| Week | Dates | Status | Deliverable |
|------|-------|--------|-------------|
| **Week 1** | Jan 16-23 | ✅ COMPLETE | Core search interface |
| **Week 2** | Jan 24-31 | 🔄 IN PROGRESS | Enhanced features |
| **Week 3** | Feb 1-7 | ⏳ UPCOMING | Deployment & testing |
| **Demo Day** | Feb 9 | 🎯 TARGET | Present to specialists |

**We are on track! Week 1 prototype is ready for testing.**
