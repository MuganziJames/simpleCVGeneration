

const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://localhost:8000"
  : "/api";
const TOTAL_STEPS = 9;

// Template Metadata
const TEMPLATE_META = {
  uk_professional_template: {
    swatch: "swatch-uk",
    desc:   "Classic serif fonts. Formal UK-style layout.",
  },
  bizarre_modern: {
    swatch: "swatch-bizarre",
    desc:   "Bold orange accents. Contemporary typography.",
  },
  minimal_professional: {
    swatch: "swatch-minimal",
    desc:   "Dark header, clean body. Understated elegance.",
  },
  bold: {
    swatch: "swatch-bold",
    desc:   "Two-column labels. Strong visual hierarchy.",
  },
  corporate_classic: {
    swatch: "swatch-corporate",
    desc:   "Monochromatic serif. Traditional corporate look.",
  },
};

// State
let currentStep = 1;
let lastPdfBlob = null;
let lastFileName = "";

// DOM References
const progressFill   = document.getElementById("progressFill");
const progressSteps  = document.getElementById("progressSteps");
const btnPrev        = document.getElementById("btnPrev");
const btnNext        = document.getElementById("btnNext");
const btnGenerate    = document.getElementById("btnGenerate");
const btnGenerateText   = document.getElementById("btnGenerateText");
const btnGenerateSpinner = document.getElementById("btnGenerateSpinner");
const successBanner  = document.getElementById("successBanner");
const errorBanner    = document.getElementById("errorBanner");
const errorMessage   = document.getElementById("errorMessage");
const downloadAgain  = document.getElementById("downloadAgain");
const templateGrid   = document.getElementById("templateGrid");
const templateInput  = document.getElementById("selectedTemplate");
const templateError  = document.getElementById("templateError");

// Step Navigation

const STEP_LABELS = [
  "Personal Info",
  "Summary",
  "Experience",
  "Education",
  "Skills",
  "Projects",
  "Certifications",
  "Extras",
  "Template",
];

function buildProgressSteps() {
  const stepper = document.getElementById("stepper");
  const wrap = document.createElement("div");
  wrap.className = "stepper__steps";
  STEP_LABELS.forEach((label, i) => {
    const num = i + 1;
    const stepEl = document.createElement("div");
    stepEl.className = "stepper__step" + (num === 1 ? " active" : "");
    stepEl.dataset.step = num;
    stepEl.innerHTML = `
      <button type="button" class="stepper__dot" aria-label="Go to step ${num}: ${label}">${num}</button>
      <span class="stepper__label">${label}</span>
    `;
    stepEl.querySelector(".stepper__dot").addEventListener("click", () => navigateTo(num));
    wrap.appendChild(stepEl);
  });
  stepper.appendChild(wrap);
}

function updateProgress(step) {
  document.querySelectorAll(".stepper__step").forEach((el) => {
    const s = parseInt(el.dataset.step, 10);
    el.classList.remove("active", "completed");
    if (s === step) el.classList.add("active");
    if (s < step)  el.classList.add("completed");
  });
}

function showStep(step) {
  document.querySelectorAll(".step").forEach((el) => {
    el.classList.toggle("hidden", parseInt(el.dataset.step, 10) !== step);
  });

  btnPrev.disabled    = step === 1;
  btnNext.classList.toggle("hidden", step === TOTAL_STEPS);
  btnGenerate.classList.toggle("hidden", step !== TOTAL_STEPS);

  updateProgress(step);
  hideBanners();
}

function navigateTo(target) {
  if (target === currentStep) return;
  if (target > currentStep) {
    if (!validateStep(currentStep)) return;
    currentStep = target;
  } else {
    currentStep = target;
  }
  showStep(currentStep);
}

btnNext.addEventListener("click", () => {
  if (!validateStep(currentStep)) return;
  if (currentStep < TOTAL_STEPS) {
    currentStep++;
    showStep(currentStep);
  }
});

btnPrev.addEventListener("click", () => {
  if (currentStep > 1) {
    currentStep--;
    showStep(currentStep);
  }
});

// Validation

function validateStep(step) {
  if (step === 1) return validatePersonalInfo();
  if (step === TOTAL_STEPS) return validateTemplate();
  return true;
}

function validatePersonalInfo() {
  let valid = true;

  const fields = [
    { id: "fullName",  msg: "Full name is required." },
    { id: "jobTitle",  msg: "Professional title is required." },
    { id: "email",     msg: "Email address is required." },
    { id: "phone",     msg: "Phone number is required." },
  ];

  fields.forEach(({ id, msg }) => {
    const el = document.getElementById(id);
    const errEl = el.closest(".field").querySelector(".field-error");
    if (!el.value.trim()) {
      showFieldError(el, errEl, msg);
      valid = false;
    } else {
      clearFieldError(el, errEl);
    }
  });

  const emailEl = document.getElementById("email");
  if (emailEl.value.trim() && !/.+@.+\..+/.test(emailEl.value.trim())) {
    const errEl = emailEl.closest(".field").querySelector(".field-error");
    showFieldError(emailEl, errEl, "Enter a valid email address.");
    valid = false;
  }

  return valid;
}

function validateTemplate() {
  if (!templateInput.value) {
    templateError.textContent = "Please select a template to continue.";
    return false;
  }
  templateError.textContent = "";
  return true;
}

function showFieldError(input, errEl, msg) {
  input.classList.add("invalid");
  if (errEl) errEl.textContent = msg;
}

function clearFieldError(input, errEl) {
  input.classList.remove("invalid");
  if (errEl) errEl.textContent = "";
}

// Dynamic Lists

document.getElementById("addExperience").addEventListener("click", () => {
  addExperienceCard();
});

function addExperienceCard(data = {}) {
  const list = document.getElementById("experienceList");
  const idx  = list.children.length;
  const card = document.createElement("div");
  card.className = "entry-card";
  card.innerHTML = `
    <div class="entry-card__header">
      <span class="entry-card__title">Position ${idx + 1}</span>
      <button type="button" class="btn-remove" title="Remove">✕</button>
    </div>
    <div class="form-grid two-col">
      <div class="field">
        <label>Position / Role</label>
        <input type="text" class="exp-position" placeholder="Job title" value="${esc(data.position || "")}" />
      </div>
      <div class="field">
        <label>Company / Organisation</label>
        <input type="text" class="exp-company" placeholder="Company or organisation" value="${esc(data.company || "")}" />
      </div>
      <div class="field">
        <label>Date Range</label>
        <input type="text" class="exp-date" placeholder="Start date – End date" value="${esc(data.date_range || "")}" />
      </div>
    </div>
    <label style="font-size:0.85rem;font-weight:500;display:block;margin:0.75rem 0 0.4rem;">
      Responsibilities &amp; Achievements
    </label>
    <div class="bullet-list"></div>
    <button type="button" class="btn-add-bullet">+ Add bullet point</button>
  `;

  card.querySelector(".btn-remove").addEventListener("click", () => {
    card.remove();
    renumberCards(list, "Position");
  });

  card.querySelector(".btn-add-bullet").addEventListener("click", () => {
    addBulletRow(card.querySelector(".bullet-list"));
  });

  list.appendChild(card);

  const bulletList = card.querySelector(".bullet-list");
  if (data.bullets && data.bullets.length) {
    data.bullets.forEach((b) => addBulletRow(bulletList, b));
  } else {
    addBulletRow(bulletList);
  }
}

document.getElementById("addEducation").addEventListener("click", () => {
  addEducationCard();
});

function addEducationCard(data = {}) {
  const list = document.getElementById("educationList");
  const idx  = list.children.length;
  const card = document.createElement("div");
  card.className = "entry-card";
  card.innerHTML = `
    <div class="entry-card__header">
      <span class="entry-card__title">Education ${idx + 1}</span>
      <button type="button" class="btn-remove" title="Remove">✕</button>
    </div>
    <div class="form-grid two-col">
      <div class="field">
        <label>Degree / Qualification</label>
        <input type="text" class="edu-degree" placeholder="Degree or qualification name" value="${esc(data.degree || "")}" />
      </div>
      <div class="field">
        <label>Institution</label>
        <input type="text" class="edu-institution" placeholder="University or institution" value="${esc(data.institution || "")}" />
      </div>
      <div class="field">
        <label>Year / Date Range</label>
        <input type="text" class="edu-year" placeholder="Graduation year or date range" value="${esc(data.year || "")}" />
      </div>
    </div>
  `;

  card.querySelector(".btn-remove").addEventListener("click", () => {
    card.remove();
    renumberCards(list, "Education");
  });

  list.appendChild(card);
}

document.getElementById("addSkill").addEventListener("click", () => {
  addSkillCard();
});

function addSkillCard(data = {}) {
  const list = document.getElementById("skillsList");
  const idx  = list.children.length;
  const card = document.createElement("div");
  card.className = "entry-card";
  card.innerHTML = `
    <div class="entry-card__header">
      <span class="entry-card__title">Skill Category ${idx + 1}</span>
      <button type="button" class="btn-remove" title="Remove">✕</button>
    </div>
    <div class="form-grid two-col">
      <div class="field">
        <label>Category Name</label>
        <input type="text" class="skill-category" placeholder="Skill group name" value="${esc(data.category || "")}" />
      </div>
      <div class="field">
        <label>Skills <span class="opt">(comma-separated)</span></label>
        <input type="text" class="skill-skills" placeholder="Skill 1, Skill 2, Skill 3" value="${esc(data.skills || "")}" />
      </div>
    </div>
  `;

  card.querySelector(".btn-remove").addEventListener("click", () => {
    card.remove();
    renumberCards(list, "Skill Category");
  });

  list.appendChild(card);
}

document.getElementById("addProject").addEventListener("click", () => {
  addProjectCard();
});

function addProjectCard(data = {}) {
  const list = document.getElementById("projectsList");
  const idx  = list.children.length;
  const card = document.createElement("div");
  card.className = "entry-card";
  card.innerHTML = `
    <div class="entry-card__header">
      <span class="entry-card__title">Project ${idx + 1}</span>
      <button type="button" class="btn-remove" title="Remove">✕</button>
    </div>
    <div class="form-grid" style="grid-template-columns:1fr;">
      <div class="field">
        <label>Project Name</label>
        <input type="text" class="proj-name" placeholder="Project title" value="${esc(data.name || "")}" />
      </div>
      <div class="field">
        <label>Technologies Used <span class="opt">(optional, comma-separated)</span></label>
        <input type="text" class="proj-tech" placeholder="Technologies used" value="${esc(data.technologies || "")}" />
      </div>
    </div>
    <label style="font-size:0.85rem;font-weight:500;display:block;margin:0.75rem 0 0.4rem;">
      What you built / what it does
    </label>
    <div class="bullet-list"></div>
    <button type="button" class="btn-add-bullet">+ Add bullet point</button>
  `;

  card.querySelector(".btn-remove").addEventListener("click", () => {
    card.remove();
    renumberCards(list, "Project");
  });

  card.querySelector(".btn-add-bullet").addEventListener("click", () => {
    addBulletRow(card.querySelector(".bullet-list"));
  });

  list.appendChild(card);

  const bulletList = card.querySelector(".bullet-list");
  if (data.bullets && data.bullets.length) {
    data.bullets.forEach((b) => addBulletRow(bulletList, b));
  } else {
    addBulletRow(bulletList);
  }
}

document.getElementById("addCertification").addEventListener("click", () => {
  addCertificationCard();
});

function addCertificationCard(data = {}) {
  const list = document.getElementById("certificationsList");
  const idx  = list.children.length;
  const card = document.createElement("div");
  card.className = "entry-card";
  card.innerHTML = `
    <div class="entry-card__header">
      <span class="entry-card__title">Certification ${idx + 1}</span>
      <button type="button" class="btn-remove" title="Remove">✕</button>
    </div>
    <div class="form-grid two-col">
      <div class="field" style="grid-column:1/-1;">
        <label>Certificate Name</label>
        <input type="text" class="cert-name" placeholder="Certificate or qualification name" value="${esc(data.name || "")}" />
      </div>
      <div class="field">
        <label>Issuing Organisation</label>
        <input type="text" class="cert-issuer" placeholder="Issuing organisation" value="${esc(data.issuer || "")}" />
      </div>
      <div class="field">
        <label>Year</label>
        <input type="text" class="cert-year" placeholder="Year obtained" value="${esc(data.year || "")}" />
      </div>
    </div>
    <label style="font-size:0.85rem;font-weight:500;display:block;margin:0.75rem 0 0.4rem;">
      Description <span class="opt">(optional bullet points)</span>
    </label>
    <div class="bullet-list"></div>
    <button type="button" class="btn-add-bullet">+ Add bullet point</button>
  `;

  card.querySelector(".btn-remove").addEventListener("click", () => {
    card.remove();
    renumberCards(list, "Certification");
  });

  card.querySelector(".btn-add-bullet").addEventListener("click", () => {
    addBulletRow(card.querySelector(".bullet-list"));
  });

  list.appendChild(card);

  const bulletList = card.querySelector(".bullet-list");
  if (data.bullets && data.bullets.length) {
    data.bullets.forEach((b) => addBulletRow(bulletList, b));
  }
}

document.getElementById("addAward").addEventListener("click", () => {
  addAwardRow();
});

function addAwardRow(value = "") {
  const list = document.getElementById("awardsList");
  const row  = document.createElement("div");
  row.className = "bullet-row";
  row.innerHTML = `
    <input type="text" placeholder="Award or recognition" value="${esc(value)}" />
    <button type="button" class="btn-remove-bullet" title="Remove">✕</button>
  `;
  row.querySelector(".btn-remove-bullet").addEventListener("click", () => row.remove());
  list.appendChild(row);
}

document.getElementById("addLanguage").addEventListener("click", () => {
  addLanguageCard();
});

function addLanguageCard(data = {}) {
  const list = document.getElementById("languagesList");
  const card = document.createElement("div");
  card.className = "entry-card";
  card.innerHTML = `
    <div class="entry-card__header">
      <span class="entry-card__title">Language</span>
      <button type="button" class="btn-remove" title="Remove">✕</button>
    </div>
    <div class="form-grid two-col">
      <div class="field">
        <label>Language</label>
        <input type="text" class="lang-language" placeholder="Language name" value="${esc(data.language || "")}" />
      </div>
      <div class="field">
        <label>Proficiency Level</label>
        <select class="lang-level">
          ${["", "Native", "Fluent", "Professional", "Conversational", "Basic"].map(
            (l) => `<option value="${l}" ${(data.level || "") === l ? "selected" : ""}>${l || "— select level —"}</option>`
          ).join("")}
        </select>
      </div>
    </div>
  `;

  card.querySelector(".btn-remove").addEventListener("click", () => card.remove());
  list.appendChild(card);
}

function addBulletRow(container, value = "") {
  const row = document.createElement("div");
  row.className = "bullet-row";
  row.innerHTML = `
    <input type="text" placeholder="Describe a responsibility or achievement" value="${esc(value)}" />
    <button type="button" class="btn-remove-bullet" title="Remove bullet">✕</button>
  `;
  row.querySelector(".btn-remove-bullet").addEventListener("click", () => row.remove());
  container.appendChild(row);
}

function renumberCards(list, label) {
  Array.from(list.children).forEach((card, i) => {
    const titleEl = card.querySelector(".entry-card__title");
    if (titleEl) titleEl.textContent = `${label} ${i + 1}`;
  });
}

// Template Cards

async function loadTemplates() {
  try {
    const res  = await fetch(`${API_BASE}/form-templates`);
    const json = await res.json();
    renderTemplateCards(json.templates);
    if (_pendingTemplateRestore) {
      selectTemplate(_pendingTemplateRestore);
      _pendingTemplateRestore = null;
    }
  } catch {
    templateGrid.innerHTML = `<p class="template-loading" style="color:var(--error);">
      Could not load templates. Make sure the backend is running at ${API_BASE}.
    </p>`;
  }
}

function renderTemplateCards(templates) {
  templateGrid.innerHTML = "";
  templates.forEach(({ key, name }) => {
    const meta  = TEMPLATE_META[key] || { swatch: "", desc: "" };
    const card  = document.createElement("div");
    card.className = "template-card";
    card.dataset.key = key;
    card.innerHTML = `
      <div class="template-card__swatch ${meta.swatch}">${name}</div>
      <div class="template-card__name">${name}</div>
      <div class="template-card__desc">${meta.desc}</div>
    `;
    card.addEventListener("click", () => selectTemplate(key));
    templateGrid.appendChild(card);
  });
}

function selectTemplate(key) {
  templateInput.value = key;
  templateError.textContent = "";
  document.querySelectorAll(".template-card").forEach((c) => {
    c.classList.toggle("selected", c.dataset.key === key);
  });
  debouncedSave();
}

// Form Collection

function collectFormData() {
  const val = (id) => (document.getElementById(id)?.value || "").trim();

  const payload = {
    full_name:  val("fullName"),
    job_title:  val("jobTitle"),
    email:      val("email"),
    phone:      val("phone"),
    location:   val("location")   || null,
    github:     val("github")     || null,
    portfolio:  val("portfolio")  || null,
    linkedin:   val("linkedin")   || null,
    summary:    val("summary")    || null,
    template:   val("selectedTemplate"),
    interests:  val("interests")  || null,
  };

  const expCards = document.querySelectorAll("#experienceList .entry-card");
  payload.experience = Array.from(expCards).map((card) => ({
    position:   card.querySelector(".exp-position")?.value.trim() || "",
    company:    card.querySelector(".exp-company")?.value.trim()  || "",
    date_range: card.querySelector(".exp-date")?.value.trim()     || "",
    bullets:    collectBullets(card),
  })).filter((e) => e.position || e.company);

  const eduCards = document.querySelectorAll("#educationList .entry-card");
  payload.education = Array.from(eduCards).map((card) => ({
    degree:      card.querySelector(".edu-degree")?.value.trim()      || "",
    institution: card.querySelector(".edu-institution")?.value.trim() || "",
    year:        card.querySelector(".edu-year")?.value.trim()        || "",
  })).filter((e) => e.degree || e.institution);

  const skillCards = document.querySelectorAll("#skillsList .entry-card");
  payload.skills = Array.from(skillCards).map((card) => ({
    category: card.querySelector(".skill-category")?.value.trim() || "",
    skills:   card.querySelector(".skill-skills")?.value.trim()   || "",
  })).filter((s) => s.category && s.skills);

  const projCards = document.querySelectorAll("#projectsList .entry-card");
  payload.projects = Array.from(projCards).map((card) => ({
    name:         card.querySelector(".proj-name")?.value.trim() || "",
    bullets:      collectBullets(card),
    technologies: card.querySelector(".proj-tech")?.value.trim() || null,
  })).filter((p) => p.name);

  const certCards = document.querySelectorAll("#certificationsList .entry-card");
  payload.certifications = Array.from(certCards).map((card) => ({
    name:    card.querySelector(".cert-name")?.value.trim()   || "",
    issuer:  card.querySelector(".cert-issuer")?.value.trim() || "",
    year:    card.querySelector(".cert-year")?.value.trim()   || "",
    bullets: collectBullets(card),
  })).filter((c) => c.name);

  const awardRows = document.querySelectorAll("#awardsList .bullet-row input");
  payload.awards = Array.from(awardRows)
    .map((i) => i.value.trim())
    .filter(Boolean);

  const langCards = document.querySelectorAll("#languagesList .entry-card");
  payload.languages = Array.from(langCards).map((card) => ({
    language: card.querySelector(".lang-language")?.value.trim() || "",
    level:    card.querySelector(".lang-level")?.value           || "",
  })).filter((l) => l.language);


  ["experience", "education", "skills", "projects", "certifications", "awards", "languages"].forEach(
    (k) => { if (!payload[k]?.length) payload[k] = null; }
  );

  return payload;
}

function collectBullets(card) {
  return Array.from(card.querySelectorAll(".bullet-list .bullet-row input"))
    .map((i) => i.value.trim())
    .filter(Boolean);
}

// Cache

const CACHE_KEY     = "cv_gen_draft";
const CACHE_VERSION = 1;

let _pendingTemplateRestore = null;
let _saveTimer              = null;

function debouncedSave() {
  clearTimeout(_saveTimer);
  _saveTimer = setTimeout(saveToCache, 900);
}

function saveToCache() {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      version: CACHE_VERSION,
      savedAt: new Date().toISOString(),
      fields: {
        fullName:  document.getElementById("fullName")?.value  || "",
        jobTitle:  document.getElementById("jobTitle")?.value  || "",
        email:     document.getElementById("email")?.value     || "",
        phone:     document.getElementById("phone")?.value     || "",
        location:  document.getElementById("location")?.value  || "",
        github:    document.getElementById("github")?.value    || "",
        portfolio: document.getElementById("portfolio")?.value || "",
        linkedin:  document.getElementById("linkedin")?.value  || "",
        summary:   document.getElementById("summary")?.value   || "",
        interests: document.getElementById("interests")?.value || "",
        template:  document.getElementById("selectedTemplate")?.value || "",
      },
      experience:     _snapExperience(),
      education:      _snapEducation(),
      skills:         _snapSkills(),
      projects:       _snapProjects(),
      certifications: _snapCertifications(),
      awards:         _snapAwards(),
      languages:      _snapLanguages(),
    }));
  } catch (err) {
    console.warn("Cache write failed:", err);
  }
}

function restoreFromCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (!data || data.version !== CACHE_VERSION) return;

    const f   = data.fields || {};
    const set = (id, v) => { const el = document.getElementById(id); if (el && v) el.value = v; };
    set("fullName",  f.fullName);
    set("jobTitle",  f.jobTitle);
    set("email",     f.email);
    set("phone",     f.phone);
    set("location",  f.location);
    set("github",    f.github);
    set("portfolio", f.portfolio);
    set("linkedin",  f.linkedin);
    set("summary",   f.summary);
    set("interests", f.interests);

    (data.experience     || []).forEach((d) => addExperienceCard(d));
    (data.education      || []).forEach((d) => addEducationCard(d));
    (data.skills         || []).forEach((d) => addSkillCard(d));
    (data.projects       || []).forEach((d) => addProjectCard(d));
    (data.certifications || []).forEach((d) => addCertificationCard(d));
    (data.awards         || []).forEach((v) => addAwardRow(v));
    (data.languages      || []).forEach((d) => addLanguageCard(d));

    if (f.template) _pendingTemplateRestore = f.template;

    const hasData = Object.values(f).some(Boolean)
      || (data.experience?.length) || (data.education?.length);
    if (hasData) {
      const notice = document.getElementById("cacheNotice");
      const textEl = notice?.querySelector(".cache-notice__text");
      if (notice && textEl) {
        const when = data.savedAt
          ? new Date(data.savedAt).toLocaleString()
          : "a previous session";
        textEl.textContent = `Draft restored from ${when}.`;
        notice.classList.remove("hidden");
      }
    }
  } catch (err) {
    console.warn("Cache restore failed:", err);
  }
}

function clearCache() {
  try { localStorage.removeItem(CACHE_KEY); } catch { }
}

// Snapshot Helpers

function _snapExperience() {
  return Array.from(document.querySelectorAll("#experienceList .entry-card")).map((c) => ({
    position:   c.querySelector(".exp-position")?.value || "",
    company:    c.querySelector(".exp-company")?.value  || "",
    date_range: c.querySelector(".exp-date")?.value     || "",
    bullets:    collectBullets(c),
  }));
}
function _snapEducation() {
  return Array.from(document.querySelectorAll("#educationList .entry-card")).map((c) => ({
    degree:      c.querySelector(".edu-degree")?.value      || "",
    institution: c.querySelector(".edu-institution")?.value || "",
    year:        c.querySelector(".edu-year")?.value        || "",
  }));
}
function _snapSkills() {
  return Array.from(document.querySelectorAll("#skillsList .entry-card")).map((c) => ({
    category: c.querySelector(".skill-category")?.value || "",
    skills:   c.querySelector(".skill-skills")?.value   || "",
  }));
}
function _snapProjects() {
  return Array.from(document.querySelectorAll("#projectsList .entry-card")).map((c) => ({
    name:         c.querySelector(".proj-name")?.value  || "",
    bullets:      collectBullets(c),
    technologies: c.querySelector(".proj-tech")?.value  || "",
  }));
}
function _snapCertifications() {
  return Array.from(document.querySelectorAll("#certificationsList .entry-card")).map((c) => ({
    name:    c.querySelector(".cert-name")?.value   || "",
    issuer:  c.querySelector(".cert-issuer")?.value || "",
    year:    c.querySelector(".cert-year")?.value   || "",
    bullets: collectBullets(c),
  }));
}
function _snapAwards() {
  return Array.from(document.querySelectorAll("#awardsList .bullet-row input"))
    .map((i) => i.value.trim()).filter(Boolean);
}
function _snapLanguages() {
  return Array.from(document.querySelectorAll("#languagesList .entry-card")).map((c) => ({
    language: c.querySelector(".lang-language")?.value || "",
    level:    c.querySelector(".lang-level")?.value    || "",
  }));
}

// Generate CV

btnGenerate.addEventListener("click", generateCV);

async function generateCV() {
  if (!validateStep(TOTAL_STEPS)) return;

  const payload = collectFormData();

  setGenerating(true);
  hideBanners();

  try {
    const res = await fetch(`${API_BASE}/generate-cv-from-form`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({ detail: "Unknown error." }));
      throw new Error(errJson.detail || `Server error ${res.status}`);
    }

    const blob = await res.blob();
    const name = payload.full_name.replace(/\s+/g, "_");
    const tpl  = payload.template.replace(/_/g, "-");
    lastFileName = `${name}_CV_${tpl}.pdf`;
    lastPdfBlob  = blob;

    triggerDownload(blob, lastFileName);
    showSuccess();
  } catch (err) {
    showError(err.message || "Could not generate CV. Please try again.");
  } finally {
    setGenerating(false);
  }
}

function triggerDownload(blob, filename) {
  const url  = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href  = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

downloadAgain.addEventListener("click", (e) => {
  e.preventDefault();
  if (lastPdfBlob) triggerDownload(lastPdfBlob, lastFileName);
});

// UI Helpers

function setGenerating(active) {
  btnGenerate.disabled = active;
  btnGenerateText.textContent = active ? "Generating…" : "Generate CV";
  btnGenerateSpinner.classList.toggle("hidden", !active);
}

function showSuccess() {
  successBanner.classList.remove("hidden");
  errorBanner.classList.add("hidden");
  successBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function showError(msg) {
  errorMessage.textContent = msg;
  errorBanner.classList.remove("hidden");
  successBanner.classList.add("hidden");
  errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideBanners() {
  successBanner.classList.add("hidden");
  errorBanner.classList.add("hidden");
}

function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Init

buildProgressSteps();
showStep(1);
restoreFromCache();
loadTemplates();

document.getElementById("btnClearCache")?.addEventListener("click", () => {
  clearCache();
  document.getElementById("cacheNotice").classList.add("hidden");
});
document.getElementById("btnDismissCache")?.addEventListener("click", () => {
  document.getElementById("cacheNotice").classList.add("hidden");
});

document.getElementById("cvForm").addEventListener("input",  debouncedSave);
document.getElementById("cvForm").addEventListener("change", debouncedSave);
