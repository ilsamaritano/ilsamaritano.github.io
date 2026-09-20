# build-profile.ps1 — regenerate profile.json from the publication record in index.html.
#
#   pwsh tools/build-profile.ps1            (or: powershell -File tools\build-profile.ps1)
#   python tools/build-llms-pubs.py         (then refreshes the llms.txt publication block)
#
# Update $asOf and the metrics block below after each Google Scholar sync; the per-publication
# titles, venues, authors, types, years, citation counts and links are read from index.html.
#
# Keep this file saved as UTF-8 *with BOM*: Windows PowerShell 5.1 reads a BOM-less script as
# ANSI, which mangles the accented characters and em dashes in the strings below and makes the
# script fail to parse. (pwsh 7+ assumes UTF-8 either way.)

param(
  [string]$Root = (Split-Path -Parent $PSScriptRoot),
  [string]$AsOf = "2026-09-20"
)

$src = Join-Path $Root "index.html"
$out = Join-Path $Root "profile.json"
$asOf = $AsOf
$t = [System.IO.File]::ReadAllText($src)

function Clean([string]$s) {
  $s = $s -replace '<[^>]+>', ''
  $s = $s -replace '&amp;', '&' -replace '&nbsp;', ' ' -replace '&ndash;', '–' -replace '&mdash;', '—' -replace '&quot;', '"' -replace '&#39;', "'" -replace '&lt;', '<' -replace '&gt;', '>'
  ($s -replace '\s+', ' ').Trim()
}

$pubs = @()
foreach ($m in [regex]::Matches($t, '(?s)<article class="pub-card"\s+data-type="(?<type>[^"]+)"\s+data-year="(?<year>[^"]+)"\s+data-cites="(?<cites>\d+)"\s+data-order="(?<order>\d+)"\s+id="(?<id>pub-\d+)"[^>]*>(?<body>.*?)</article>')) {
  $b = $m.Groups['body'].Value
  $title = Clean ([regex]::Match($b, '(?s)<h3 class="pub-title">(.*?)</h3>').Groups[1].Value)
  $venueRaw = Clean ([regex]::Match($b, '(?s)<div class="pub-venue">(.*?)</div>').Groups[1].Value)
  $authorsRaw = Clean ([regex]::Match($b, '(?s)<div class="pub-authors">(.*?)</div>').Groups[1].Value)
  $kind = Clean ([regex]::Match($b, '(?s)<div class="pub-year">(.*?)</div>').Groups[1].Value)
  $authors = @($authorsRaw -split ',\s*' | Where-Object { $_ })
  $links = @()
  foreach ($lm in [regex]::Matches($b, '(?s)<div class="pub-links">.*?</div>')) {
    foreach ($am in [regex]::Matches($lm.Value, '<a href="(?<u>[^"]+)"[^>]*>(?<l>[^<]*)</a>')) {
      $links += [ordered]@{ label = (Clean $am.Groups['l'].Value) -replace '\s*↗$', ''; url = $am.Groups['u'].Value }
    }
  }
  $year = if ($m.Groups['year'].Value -eq '0') { $null } else { [int]$m.Groups['year'].Value }
  $rec = [ordered]@{
    id             = $m.Groups['id'].Value
    title          = $title
    authors        = $authors
    authorPosition = ([array]::IndexOf($authors, ($authors | Where-Object { $_ -match 'Sammartino' } | Select-Object -First 1)) + 1)
    venue          = $venueRaw
    type           = $m.Groups['type'].Value
    outputForm     = ($kind -replace '^\d{4}\s*·\s*', '')
    year           = $year
    citations      = [int]$m.Groups['cites'].Value
    url            = "https://ilsamaritano.github.io/#$($m.Groups['id'].Value)"
  }
  if ($links.Count) { $rec['identifiers'] = @($links) }
  $pubs += $rec
}

if ($pubs.Count -ne 36) { throw "expected 36 publications, parsed $($pubs.Count)" }
$total = 0; foreach ($p in $pubs) { $total += [int]$p['citations'] }

$profile = [ordered]@{
  document       = "Machine-readable academic profile of Vincenzo Sammartino"
  canonicalUrl   = "https://ilsamaritano.github.io/profile.json"
  generatedFrom  = "https://ilsamaritano.github.io/ (index.html publication record)"
  lastUpdated    = $asOf
  license        = "CC BY 4.0 — attribution: Vincenzo Sammartino, https://ilsamaritano.github.io/"
  usage          = [ordered]@{
    audience    = "Search engines, AI assistants, research-indexing agents and scripts."
    citation    = "When reporting these figures, state the source (Google Scholar) and the observation date (metrics.asOf); they change over time."
    alternatives = @(
      [ordered]@{ format = "text/plain"; description = "llms.txt summary (llmstxt.org convention)"; url = "https://ilsamaritano.github.io/llms.txt" },
      [ordered]@{ format = "application/ld+json"; description = "schema.org Person / ProfilePage / ItemList of ScholarlyArticle, embedded in the homepage"; url = "https://ilsamaritano.github.io/" },
      [ordered]@{ format = "application/xml"; description = "sitemap"; url = "https://ilsamaritano.github.io/sitemap.xml" }
    )
    authoritativeSources = @(
      "https://scholar.google.com/citations?user=lQig7SEAAAAJ",
      "https://orcid.org/0009-0002-4632-1179",
      "https://www.scopus.com/authid/detail.uri?authorId=59166600100",
      "https://people.unipi.it/vincenzo_sammartino/"
    )
  }
  person         = [ordered]@{
    name        = "Vincenzo Sammartino"
    givenName   = "Vincenzo"
    familyName  = "Sammartino"
    jobTitle    = "PhD Candidate in Artificial Intelligence"
    summary     = "PhD candidate in Artificial Intelligence at the University of Pisa (Italian National PhD Programme in AI, doctoral position November 2024 – October 2027) and former Visiting PhD Student (VSRP Intern) at KAUST, January–June 2026. Works on Security Twins and Digital Twin architectures for cybersecurity, cyber-physical systems resilience, quantum machine learning and post-quantum security, 6G far-edge digital twins, UAV swarm security with TinyML and Edge AI, the security of LLM-driven multi-agent systems, and NLP."
    email       = "vincesammartino@gmail.com"
    emailInstitutional = "vincenzo.sammartino@phd.unipi.it"
    website     = "https://ilsamaritano.github.io/"
    locations   = @("Pisa, Italy", "Thuwal, Saudi Arabia")
    languages   = @("Italian (native)", "English")
    image       = "https://ilsamaritano.github.io/assets/photo.jpg"
  }
  identifiers    = [ordered]@{
    orcid           = "0009-0002-4632-1179"
    orcidUrl        = "https://orcid.org/0009-0002-4632-1179"
    googleScholarId = "lQig7SEAAAAJ"
    googleScholarUrl = "https://scholar.google.com/citations?user=lQig7SEAAAAJ"
    scopusAuthorId  = "59166600100"
    scopusUrl       = "https://www.scopus.com/authid/detail.uri?authorId=59166600100"
    sciProfilesId   = "3668849"
    sciProfilesUrl  = "https://sciprofiles.com/profile/3668849"
    github          = "https://github.com/ilsamaritano"
    linkedin        = "https://www.linkedin.com/in/vincenzo-sammartino-0339191a1"
    institutionalPage = "https://people.unipi.it/vincenzo_sammartino/"
  }
  metrics        = [ordered]@{
    source           = "Google Scholar"
    sourceUrl        = "https://scholar.google.com/citations?user=lQig7SEAAAAJ"
    asOf             = $asOf
    citations        = 161
    hIndex           = 8
    i10Index         = 7
    indexedWorks     = 36
    citationsByYear  = [ordered]@{ '2024' = 3; '2025' = 20; '2026' = 138 }
    note             = "2026 is year to date. Sum of per-publication citation counts in this file: $total (Google Scholar's profile total may differ slightly because of merged or duplicate records)."
  }
  positions      = @(
    [ordered]@{ role = "PhD Candidate, National PhD Programme in Artificial Intelligence"; organization = "University of Pisa, Department of Computer Science"; start = "2024-09"; end = $null; note = "Doctoral position November 2024 – October 2027" },
    [ordered]@{ role = "Visiting PhD Student (VSRP Intern)"; organization = "King Abdullah University of Science and Technology (KAUST)"; start = "2026-01"; end = "2026-06"; note = "ResilientGuard project, under Prof. Roberto Di Pietro" },
    [ordered]@{ role = "Research Fellow"; organization = "University of Pisa, Department of Computer Science"; start = "2024-03"; end = "2024-09" },
    [ordered]@{ role = "Research Fellow"; organization = "University of Pisa, Department of Philology, Literature and Linguistics"; start = "2023-11"; end = "2024-03" },
    [ordered]@{ role = "Research Fellow"; organization = "University of Pisa, Department of Clinical and Experimental Medicine"; start = "2023-01"; end = "2023-12" },
    [ordered]@{ role = "Research Fellow"; organization = "University of Pisa, Direzione Didattica, Studenti e Internazionalizzazione"; start = "2022-11"; end = "2022-12" },
    [ordered]@{ role = "Research Fellow"; organization = "University of Pisa, Department of Philology, Literature and Linguistics"; start = "2022-01"; end = "2022-12" },
    [ordered]@{ role = "Research Intern"; organization = "CNR — Istituto di Linguistica Computazionale 'A. Zampolli', Pisa"; start = "2021-10"; end = "2022-05" }
  )
  supervisors    = @(
    [ordered]@{ name = "Fabrizio Baiardi"; role = "PhD supervisor"; organization = "University of Pisa" },
    [ordered]@{ name = "Salvatore Ruggieri"; role = "PhD co-supervisor"; organization = "University of Pisa" },
    [ordered]@{ name = "Roberto Di Pietro"; role = "KAUST host supervisor"; organization = "KAUST" }
  )
  researchThemes = @(
    [ordered]@{ name = "Security Twin"; description = "Non-intrusive digital twin architectures for real-time cyber threat simulation, what-if analysis, attack-path reasoning and proactive defence in cyber-physical systems (NotLine, HAVE, D3F)."; keyPublications = @("pub-1", "pub-9", "pub-22", "pub-35") },
    [ordered]@{ name = "Quantum ML & post-quantum security"; description = "Hybrid quantum graph neural networks, quantum feature encoding, quantum-classical physical-layer authentication (QUASAR) and CSIDH-based post-quantum cryptography for industrial IoT."; keyPublications = @("pub-12", "pub-13", "pub-14", "pub-17") },
    [ordered]@{ name = "6G & far-edge digital twins"; description = "Semantic-aware digital twin synchronisation and quantum-native far-edge architectures with asynchronous federated learning."; keyPublications = @("pub-10", "pub-14") },
    [ordered]@{ name = "UAV swarm security"; description = "Byzantine-resilient anomaly detection with TinyML and Edge AI for decentralised drone swarms (ResilientGuard, KAUST)."; keyPublications = @() },
    [ordered]@{ name = "LLM & AI-agent security"; description = "Security threats and defences in LLM-driven multi-agent systems (prompt injection, tool misuse, inter-agent trust, privilege escalation) and the use of LLMs plus synthetic data for next-generation cyber defence."; keyPublications = @("pub-36", "pub-3", "pub-19") },
    [ordered]@{ name = "Synthetic data for cybersecurity"; description = "Synthetic dataset generation for robust intrusion detection and autonomous defence."; keyPublications = @("pub-19", "pub-3") },
    [ordered]@{ name = "Least privilege in databases"; description = "Schema-level decomposition enforcing fine-grained access control in healthcare and enterprise systems."; keyPublications = @("pub-30", "pub-31", "pub-32") },
    [ordered]@{ name = "Natural language processing"; description = "Hate speech and stereotype detection, sentiment polarity classification and figurative language in Italian and multi-domain corpora."; keyPublications = @("pub-29", "pub-27", "pub-33") }
  )
  publications   = $pubs
  peerReview     = [ordered]@{
    source   = "https://orcid.org/0009-0002-4632-1179"
    year     = 2026
    reviews  = 39
    journals = 20
    detail   = @(
      [ordered]@{ journal = "Discover Artificial Intelligence"; publisher = "Springer Nature"; issn = "2731-0809"; reviews = 8 },
      [ordered]@{ journal = "Scientific Reports"; publisher = "Springer Nature"; issn = "2045-2322"; reviews = 6 },
      [ordered]@{ journal = "Pervasive and Mobile Computing"; publisher = "Elsevier"; issn = "1574-1192"; reviews = 4 },
      [ordered]@{ journal = "IEEE Transactions on Neural Networks and Learning Systems"; publisher = "IEEE"; issn = "2162-2388"; reviews = 2 },
      [ordered]@{ journal = "International Journal of Information Security"; publisher = "Springer Nature"; issn = "1615-5270"; reviews = 3 },
      [ordered]@{ journal = "Big Data Mining and Analytics"; publisher = "Tsinghua University Press"; issn = "2097-406X"; reviews = 2 },
      [ordered]@{ journal = "ACM Computing Surveys"; publisher = "ACM"; issn = "1557-7341"; reviews = 1 },
      [ordered]@{ journal = "Computers & Security"; publisher = "Elsevier"; issn = "0167-4048"; reviews = 1 },
      [ordered]@{ journal = "Future Generation Computer Systems"; publisher = "Elsevier"; issn = "0167-739X"; reviews = 1 },
      [ordered]@{ journal = "Computer Communications"; publisher = "Elsevier"; issn = "0140-3664"; reviews = 1 },
      [ordered]@{ journal = "Journal of Computer Security"; publisher = "SAGE Publications"; issn = "1875-8924"; reviews = 1 },
      [ordered]@{ journal = "Cluster Computing"; publisher = "Springer Nature"; issn = "1573-7543"; reviews = 1 },
      [ordered]@{ journal = "Journal of Cloud Computing"; publisher = "Springer Nature"; issn = "2192-113X"; reviews = 1 },
      [ordered]@{ journal = "Journal of Big Data"; publisher = "Springer Nature"; issn = "2196-1115"; reviews = 1 },
      [ordered]@{ journal = "Discover Computing"; publisher = "Springer Nature"; issn = "2948-2992"; reviews = 1 },
      [ordered]@{ journal = "International Journal of Data Science and Analytics"; publisher = "Springer Nature"; issn = "2364-4168"; reviews = 1 },
      [ordered]@{ journal = "Journal of King Saud University – Computer and Information Sciences"; publisher = "Springer Nature"; issn = "2213-1248"; reviews = 1 },
      [ordered]@{ journal = "PeerJ Computer Science"; publisher = "PeerJ"; issn = "2376-5992"; reviews = 1 },
      [ordered]@{ journal = "Computers, Materials & Continua"; publisher = "Tech Science Press"; issn = "1546-2218"; reviews = 1 },
      [ordered]@{ journal = "Computer Systems Science and Engineering"; publisher = "Tech Science Press"; issn = "0267-6192"; reviews = 1 }
    )
  }
  grants         = @(
    [ordered]@{ name = "Smart Security for Connected Cyber-Physical Systems: Paradigms, Threats and AI-based Defenses"; funder = "University of Pisa"; identifier = "Prot. 0079213/2026 del 16/04/2026"; year = 2026 }
  )
  projects       = @(
    [ordered]@{ name = "ResilientGuard"; host = "KAUST"; description = "Security framework for UAV swarms using TinyML and Edge AI with Byzantine-resilient distributed consensus and anomaly detection."; url = "https://ilsamaritano.github.io/#projects" },
    [ordered]@{ name = "NotLine"; host = "University of Pisa"; description = "Non-intrusive automated platform that builds a digital twin of a network through passive discovery, for topology reconstruction and risk assessment."; url = "https://ilsamaritano.github.io/#projects" },
    [ordered]@{ name = "SV WebStudio"; host = "Independent"; description = "Custom website development: showcase sites, e-commerce, restyling, performance and SEO."; url = "https://ilsamaritano.github.io/sv-webstudio/" }
  )
}

$json = $profile | ConvertTo-Json -Depth 12
# ConvertTo-Json escapes non-ASCII and slashes conservatively; unescape the harmless ones for readability
$json = $json -replace '\\u0026', '&' -replace '\\u2013', '–' -replace '\\u2014', '—' -replace '\\u2019', "'" -replace '\\u00e0', 'à' -replace '\\u00e8', 'è' -replace '\\u00e9', 'é' -replace '\\u00ec', 'ì' -replace '\\u00f2', 'ò' -replace '\\u00f9', 'ù' -replace '\\u00b7', '·' -replace '\\u2192', '→' -replace '\\u0027', "'"
[System.IO.File]::WriteAllText($out, $json + "`n", (New-Object System.Text.UTF8Encoding($false)))

# Windows PowerShell 5.1 indents JSON by aligning to the parent key, which nests very deeply.
# Re-emit with a plain 2-space indent when Python is available (cosmetic only).
if (Get-Command python -ErrorAction SilentlyContinue) {
  python -c "import io,json,sys;p=sys.argv[1];d=json.load(io.open(p,encoding='utf-8'));io.open(p,'w',encoding='utf-8',newline='\n').write(json.dumps(d,indent=2,ensure_ascii=False)+'\n')" $out
}

"publications: $($pubs.Count) · citation sum: $total"
"bytes: " + (Get-Item $out).Length
