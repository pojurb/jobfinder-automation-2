#!/usr/bin/env python3
"""
Dashboard Compiler
Reads all ./jobs/*.md files and compiles a standalone interactive HTML dashboard.
Uses only Python standard library.
"""

import os
import re
import json
from datetime import datetime

JOBS_DIR = "jobs"
OUTPUT_FILE = "index.html"


def parse_markdown(filepath):
    """Parse a markdown file into metadata dict + body string."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    parts = re.split(r"^---\s*$", content, maxsplit=2, flags=re.MULTILINE)

    if len(parts) >= 3:
        frontmatter = parts[1].strip()
        body = parts[2].strip()
    else:
        frontmatter = ""
        body = content.strip()

    metadata = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key == "match_score":
                try:
                    value = int(value)
                except ValueError:
                    value = 0
            metadata[key] = value

    return {"metadata": metadata, "body": body}


def main():
    if not os.path.exists(JOBS_DIR):
        os.makedirs(JOBS_DIR)

    jobs = []
    for filename in sorted(os.listdir(JOBS_DIR)):
        if filename.endswith(".md"):
            filepath = os.path.join(JOBS_DIR, filename)
            jobs.append(parse_markdown(filepath))

    jobs_json = json.dumps(jobs, ensure_ascii=False)
    build_ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Collect unique sources for the filter dropdown
    sources = sorted(set(j["metadata"].get("source", "") for j in jobs if j["metadata"].get("source")))
    sources_options = "".join(f'<option value="{s}">{s}</option>' for s in sources)

    html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Tracker Dashboard</title>
    <meta name="description" content="Personal job tracking dashboard — track, score, and manage job applications.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    fontFamily: {{ sans: ['Inter', 'system-ui', 'sans-serif'] }},
                }}
            }}
        }}
    </script>
    <style>
        body {{ font-family: 'Inter', system-ui, sans-serif; }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #475569; }}
        .card-shine {{ position: relative; overflow: hidden; }}
        .card-shine::before {{
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
            transition: left 0.6s ease;
        }}
        .card-shine:hover::before {{ left: 100%; }}
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(16px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .animate-card {{ animation: fadeInUp 0.4s ease forwards; opacity: 0; }}
        @keyframes pulse-dot {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.4; }}
        }}
        .new-pulse {{ animation: pulse-dot 2s ease-in-out infinite; }}
    </style>
</head>
<body class="bg-[#0a0f1a] text-slate-200 min-h-screen">

    <!-- Background Gradient Blobs -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-40 -left-40 w-[500px] h-[500px] bg-indigo-600/5 rounded-full blur-3xl"></div>
    </div>

    <div class="relative max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-10 py-8">

        <!-- Header -->
        <header class="mb-10">
            <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-8">
                <div>
                    <div class="flex items-center gap-3 mb-2">
                        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                        </div>
                        <h1 class="text-3xl font-extrabold text-white tracking-tight">Job Tracker</h1>
                    </div>
                    <p class="text-slate-500 text-sm font-medium ml-[52px]">Last compiled: {build_ts}</p>
                </div>

                <!-- Metrics -->
                <div class="flex gap-3 w-full lg:w-auto">
                    <div class="flex-1 bg-slate-800/40 backdrop-blur rounded-2xl p-4 border border-slate-700/40 text-center min-w-[100px]">
                        <div class="text-2xl font-bold text-white mb-0.5" id="m-total">0</div>
                        <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Total</div>
                    </div>
                    <div class="flex-1 bg-slate-800/40 backdrop-blur rounded-2xl p-4 border border-slate-700/40 text-center min-w-[100px]">
                        <div class="text-2xl font-bold text-emerald-400 mb-0.5" id="m-high">0</div>
                        <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">High Match</div>
                    </div>
                    <div class="flex-1 bg-slate-800/40 backdrop-blur rounded-2xl p-4 border border-slate-700/40 text-center min-w-[100px]">
                        <div class="text-2xl font-bold text-blue-400 mb-0.5" id="m-applied">0</div>
                        <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Applied</div>
                    </div>
                    <div class="flex-1 bg-slate-800/40 backdrop-blur rounded-2xl p-4 border border-slate-700/40 text-center min-w-[100px]">
                        <div class="text-2xl font-bold text-amber-400 mb-0.5" id="m-new">0</div>
                        <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">New Today</div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Controls Bar -->
        <div class="flex flex-col xl:flex-row gap-3 mb-8 bg-slate-800/20 p-2 rounded-2xl border border-slate-700/30 backdrop-blur-sm">
            <!-- Search -->
            <div class="relative flex-1">
                <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <svg class="h-4 w-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </div>
                <input type="text" id="search-input" placeholder="Search title or company..." class="w-full bg-slate-900/60 border border-slate-700/30 rounded-xl pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-transparent text-sm transition-all placeholder:text-slate-600">
            </div>
            <div class="flex flex-wrap gap-2">
                <!-- Status filter -->
                <select id="filter-status" class="bg-slate-900/60 border border-slate-700/30 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/40 text-sm font-medium cursor-pointer">
                    <option value="All">All Statuses</option>
                    <option value="Ready to Apply">Ready to Apply</option>
                    <option value="Applied">Applied</option>
                    <option value="Interviewing">Interviewing</option>
                    <option value="Archived">Archived</option>
                </select>
                <!-- Score filter -->
                <select id="filter-score" class="bg-slate-900/60 border border-slate-700/30 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/40 text-sm font-medium cursor-pointer">
                    <option value="All">All Scores</option>
                    <option value="High">High Match (90+)</option>
                    <option value="Good">Good Match (50+)</option>
                    <option value="Low">Low Match (<50)</option>
                </select>
                <!-- Work Type filter -->
                <select id="filter-worktype" class="bg-slate-900/60 border border-slate-700/30 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/40 text-sm font-medium cursor-pointer">
                    <option value="All">All Work Types</option>
                    <option value="Remote">Remote</option>
                    <option value="Hybrid">Hybrid</option>
                    <option value="On-site">On-site</option>
                </select>
                <!-- Source filter -->
                <select id="filter-source" class="bg-slate-900/60 border border-slate-700/30 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/40 text-sm font-medium cursor-pointer">
                    <option value="All">All Sources</option>
                    {sources_options}
                </select>
                <!-- Sort toggles -->
                <div class="flex bg-slate-900/60 border border-slate-700/30 rounded-xl overflow-hidden p-1">
                    <button id="sort-score" class="px-4 py-2 text-xs font-semibold rounded-lg text-slate-400 hover:text-white transition-all" title="Sort by match score">Score ↓</button>
                    <button id="sort-date" class="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600/20 text-blue-400 transition-all" title="Sort by date added">Date ↓</button>
                </div>
            </div>
        </div>

        <!-- Job count -->
        <div class="mb-4 text-xs text-slate-500 font-medium px-1" id="result-count"></div>

        <!-- Grid -->
        <div id="jobs-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        </div>

        <!-- Modal -->
        <div id="modal-overlay" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4 transition-opacity duration-300 opacity-0">
            <div id="modal-box" class="bg-[#111827] border border-slate-700/60 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl shadow-black/40 transform scale-95 transition-transform duration-300">
                <!-- Modal Header -->
                <div class="p-6 md:p-8 border-b border-slate-800 flex justify-between items-start">
                    <div class="pr-8 flex-1">
                        <div class="flex items-center gap-2 mb-3">
                            <span id="md-source-badge" class="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-slate-800 text-slate-400 border border-slate-700/50"></span>
                            <span id="md-new-badge" class="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hidden">NEW</span>
                        </div>
                        <h2 id="md-title" class="text-2xl font-bold text-white mb-2 leading-tight"></h2>
                        <p id="md-company" class="text-lg text-blue-400 font-medium flex items-center gap-2">
                            <svg class="w-4 h-4 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                            <span></span>
                        </p>
                    </div>
                    <button id="close-modal" class="text-slate-500 hover:text-white bg-slate-800/60 hover:bg-slate-700 p-2.5 rounded-xl transition-colors flex-shrink-0">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
                <!-- Modal Body -->
                <div class="p-6 md:p-8 flex-1 overflow-y-auto">
                    <!-- Metadata chips -->
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                        <div class="bg-slate-800/50 px-4 py-3 rounded-xl border border-slate-700/40">
                            <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Score</div>
                            <div id="md-score" class="font-bold text-xl"></div>
                        </div>
                        <div class="bg-slate-800/50 px-4 py-3 rounded-xl border border-slate-700/40">
                            <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Status</div>
                            <div id="md-status" class="font-medium text-sm text-slate-200"></div>
                        </div>
                        <div class="bg-slate-800/50 px-4 py-3 rounded-xl border border-slate-700/40">
                            <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Location</div>
                            <div id="md-location" class="font-medium text-sm text-slate-200"></div>
                        </div>
                        <div class="bg-slate-800/50 px-4 py-3 rounded-xl border border-slate-700/40">
                            <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Work Type</div>
                            <div id="md-worktype" class="font-medium text-sm text-slate-200"></div>
                        </div>
                    </div>
                    <div class="flex gap-3 mb-6">
                        <div class="bg-slate-800/50 px-4 py-3 rounded-xl border border-slate-700/40 flex-1">
                            <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Date Added</div>
                            <div id="md-date" class="font-medium text-sm text-slate-200"></div>
                        </div>
                        <div class="bg-slate-800/50 px-4 py-3 rounded-xl border border-slate-700/40 flex-1">
                            <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-1">Source</div>
                            <div id="md-source" class="font-medium text-sm text-slate-200"></div>
                        </div>
                    </div>

                    <!-- CTA -->
                    <a id="md-url" href="#" target="_blank" class="flex items-center justify-center gap-2 w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold py-3 px-4 rounded-xl mb-6 transition-all shadow-lg shadow-blue-600/20">
                        View Original Posting
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                    </a>

                    <!-- Notes -->
                    <div>
                        <h4 class="text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-3 flex items-center gap-2">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                            Notes &amp; Details
                        </h4>
                        <div id="md-body" class="text-slate-300 text-sm leading-relaxed bg-slate-900/40 rounded-xl p-5 border border-slate-700/30"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    (function() {{
        'use strict';

        const DATA = {jobs_json};
        const TODAY = new Date().toISOString().slice(0, 10);

        // State
        let sortBy = 'date';
        let filterStatus = 'All';
        let filterSource = 'All';
        let filterScore = 'All';
        let filterWorkType = 'All';
        let searchQuery = '';
        let visible = [];

        // DOM refs
        const grid        = document.getElementById('jobs-grid');
        const searchEl    = document.getElementById('search-input');
        const statusEl    = document.getElementById('filter-status');
        const sourceEl    = document.getElementById('filter-source');
        const scoreEl     = document.getElementById('filter-score');
        const workTypeEl  = document.getElementById('filter-worktype');
        const sortScoreEl = document.getElementById('sort-score');
        const sortDateEl  = document.getElementById('sort-date');
        const resultCount = document.getElementById('result-count');

        const overlay  = document.getElementById('modal-overlay');
        const modalBox = document.getElementById('modal-box');
        const closeBtn = document.getElementById('close-modal');

        // ─── Helpers ─────────────────────────────────────
        function scoreColor(s) {{
            if (s >= 90) return ['bg-emerald-500/10','text-emerald-400','border-emerald-500/20'];
            if (s >= 70) return ['bg-blue-500/10','text-blue-400','border-blue-500/20'];
            if (s >= 50) return ['bg-amber-500/10','text-amber-400','border-amber-500/20'];
            return ['bg-slate-700/30','text-slate-400','border-slate-600/30'];
        }}

        function sourceIcon(src) {{
            const icons = {{
                'RemoteOK':'🌐','Hacker News':'🟧','LinkedIn':'🔗',
                'Indeed':'🔵','Glassdoor':'🟢','JobStreet':'🟣'
            }};
            return icons[src] || '📋';
        }}

        function isNew(dateStr) {{
            return dateStr === TODAY;
        }}

        function mdToHtml(text) {{
            if (!text) return '<p class="text-slate-500 italic">No notes available.</p>';
            let h = text
                .replace(/^### (.*)$/gm, '<h3 class="text-base font-bold text-white mt-5 mb-2">$1</h3>')
                .replace(/^## (.*)$/gm, '<h2 class="text-lg font-bold text-white mt-6 mb-3">$1</h2>')
                .replace(/^# (.*)$/gm, '<h1 class="text-xl font-bold text-white mt-7 mb-4">$1</h1>')
                .replace(/\\*\\*(.+?)\\*\\*/g, '<strong class="text-white">$1</strong>')
                .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
                .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" class="text-blue-400 hover:underline">$1</a>')
                .replace(/^- (.*)$/gm, '<li class="ml-4 list-disc mb-1 marker:text-blue-500/60">$1</li>');
            // Wrap consecutive <li> in <ul>
            h = h.replace(/(<li[^>]*>.*?<\\/li>\\n?)+/g, function(m) {{
                return '<ul class="mb-4 space-y-1">' + m + '</ul>';
            }});
            // Wrap remaining plain text in <p>
            h = h.split('\\n\\n').map(function(p) {{
                p = p.trim();
                if (!p || p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<li')) return p;
                return '<p class="mb-3">' + p.replace(/\\n/g, '<br>') + '</p>';
            }}).join('');
            return h;
        }}

        // ─── Metrics ────────────────────────────────────
        function updateMetrics() {{
            document.getElementById('m-total').textContent = DATA.length;
            document.getElementById('m-high').textContent = DATA.filter(j => (j.metadata.match_score || 0) >= 90).length;
            document.getElementById('m-applied').textContent = DATA.filter(j => j.metadata.status === 'Applied').length;
            document.getElementById('m-new').textContent = DATA.filter(j => isNew(j.metadata.date_added)).length;
        }}

        // ─── Render Grid ────────────────────────────────
        function render() {{
            visible = DATA.filter(function(j) {{
                const m = j.metadata;
                const q = searchQuery.toLowerCase();
                const matchText = !q || (m.title||'').toLowerCase().includes(q) || (m.company||'').toLowerCase().includes(q);
                const matchStatus = filterStatus === 'All' || m.status === filterStatus;
                const matchSource = filterSource === 'All' || m.source === filterSource;
                
                const scoreValue = m.match_score || 0;
                const matchScore = filterScore === 'All' || 
                                   (filterScore === 'High' && scoreValue >= 90) || 
                                   (filterScore === 'Good' && scoreValue >= 50 && scoreValue < 90) || 
                                   (filterScore === 'Low' && scoreValue < 50);

                const matchWorkType = filterWorkType === 'All' || 
                                      (m.work_type && m.work_type.toLowerCase().includes(filterWorkType.toLowerCase()));

                return matchText && matchStatus && matchSource && matchScore && matchWorkType;
            }});

            visible.sort(function(a, b) {{
                if (sortBy === 'score') return (b.metadata.match_score||0) - (a.metadata.match_score||0);
                return (b.metadata.date_added||'').localeCompare(a.metadata.date_added||'');
            }});

            resultCount.textContent = visible.length + ' job' + (visible.length !== 1 ? 's' : '') + ' found';

            if (!visible.length) {{
                grid.innerHTML = '<div class="col-span-full py-20 flex flex-col items-center text-slate-600"><svg class="w-14 h-14 mb-4 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg><p class="text-base font-medium">No matching jobs found.</p></div>';
                return;
            }}

            grid.innerHTML = visible.map(function(job, i) {{
                const m = job.metadata;
                const score = m.match_score || 0;
                const sc = scoreColor(score);
                const isNewJob = isNew(m.date_added);
                const delay = Math.min(i * 40, 600);
                const loc = m.location && m.location !== 'See posting' && m.location !== 'Unknown' ? m.location : '';
                const wt = m.work_type && m.work_type !== 'See posting' && m.work_type !== 'Unknown' ? m.work_type : '';

                return '<div class="card-shine animate-card bg-[#111827]/80 border border-slate-700/40 rounded-2xl p-5 hover:border-slate-500/60 hover:shadow-xl hover:shadow-black/20 hover:-translate-y-0.5 transition-all duration-300 cursor-pointer flex flex-col h-full" style="animation-delay:' + delay + 'ms" onclick="window._openModal(' + i + ')">'
                    + '<div class="flex justify-between items-start mb-4">'
                    +   '<div class="flex items-center gap-2">'
                    +     '<span class="text-sm font-bold px-2.5 py-1 rounded-lg border ' + sc.join(' ') + '">' + score + '</span>'
                    +     (isNewJob ? '<span class="new-pulse text-[9px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">NEW</span>' : '')
                    +   '</div>'
                    +   '<span class="text-[10px] font-semibold text-slate-400 px-2.5 py-1 bg-slate-800/60 rounded-lg border border-slate-700/40">' + (m.status || 'Unknown') + '</span>'
                    + '</div>'
                    + '<h3 class="text-sm font-bold text-white mb-1.5 line-clamp-2 leading-snug hover:text-blue-400 transition-colors">' + (m.title || 'Untitled') + '</h3>'
                    + '<p class="text-xs text-slate-400 font-medium mb-3">' + (m.company || 'Unknown') + '</p>'
                    + (loc || wt ? '<div class="flex flex-wrap gap-1.5 mb-3">' + (loc ? '<span class="text-[10px] text-slate-500 bg-slate-800/40 px-2 py-0.5 rounded-md">📍 ' + loc + '</span>' : '') + (wt ? '<span class="text-[10px] text-slate-500 bg-slate-800/40 px-2 py-0.5 rounded-md">' + wt + '</span>' : '') + '</div>' : '')
                    + '<div class="mt-auto pt-3 border-t border-slate-800/60 flex justify-between items-center text-[10px] text-slate-600 font-medium">'
                    +   '<span>' + (m.date_added || '') + '</span>'
                    +   '<span>' + sourceIcon(m.source) + ' ' + (m.source || '') + '</span>'
                    + '</div>'
                    + '</div>';
            }}).join('');
        }}

        // ─── Modal ──────────────────────────────────────
        window._openModal = function(idx) {{
            const job = visible[idx];
            if (!job) return;
            const m = job.metadata;
            const score = m.match_score || 0;
            const sc = scoreColor(score);

            document.getElementById('md-title').textContent = m.title || 'Untitled';
            document.getElementById('md-company').querySelector('span').textContent = m.company || 'Unknown';

            const scoreEl = document.getElementById('md-score');
            scoreEl.textContent = score;
            scoreEl.className = 'font-bold text-xl ' + sc[1];

            document.getElementById('md-status').textContent = m.status || 'N/A';
            document.getElementById('md-location').textContent = m.location || 'N/A';
            document.getElementById('md-worktype').textContent = m.work_type || 'N/A';
            document.getElementById('md-date').textContent = m.date_added || 'N/A';
            document.getElementById('md-source').textContent = (m.source ? sourceIcon(m.source) + ' ' + m.source : 'N/A');

            const srcBadge = document.getElementById('md-source-badge');
            srcBadge.textContent = m.source || 'Manual';

            const newBadge = document.getElementById('md-new-badge');
            newBadge.classList.toggle('hidden', !isNew(m.date_added));

            const urlEl = document.getElementById('md-url');
            if (m.url) {{ urlEl.href = m.url; urlEl.style.display = 'flex'; }}
            else {{ urlEl.style.display = 'none'; }}

            document.getElementById('md-body').innerHTML = mdToHtml(job.body);

            overlay.classList.remove('hidden');
            void overlay.offsetWidth;
            overlay.classList.remove('opacity-0');
            modalBox.classList.remove('scale-95');
        }};

        function closeModal() {{
            overlay.classList.add('opacity-0');
            modalBox.classList.add('scale-95');
            setTimeout(function() {{ overlay.classList.add('hidden'); }}, 300);
        }}

        closeBtn.addEventListener('click', closeModal);
        overlay.addEventListener('click', function(e) {{ if (e.target === overlay) closeModal(); }});
        document.addEventListener('keydown', function(e) {{ if (e.key === 'Escape') closeModal(); }});

        // ─── Event Bindings ─────────────────────────────
        searchEl.addEventListener('input', function(e) {{ searchQuery = e.target.value; render(); }});
        statusEl.addEventListener('change', function(e) {{ filterStatus = e.target.value; render(); }});
        sourceEl.addEventListener('change', function(e) {{ filterSource = e.target.value; render(); }});
        scoreEl.addEventListener('change', function(e) {{ filterScore = e.target.value; render(); }});
        workTypeEl.addEventListener('change', function(e) {{ filterWorkType = e.target.value; render(); }});

        sortScoreEl.addEventListener('click', function() {{
            sortBy = 'score';
            sortScoreEl.className = 'px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600/20 text-blue-400 transition-all';
            sortDateEl.className = 'px-4 py-2 text-xs font-semibold rounded-lg text-slate-400 hover:text-white transition-all';
            render();
        }});
        sortDateEl.addEventListener('click', function() {{
            sortBy = 'date';
            sortDateEl.className = 'px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600/20 text-blue-400 transition-all';
            sortScoreEl.className = 'px-4 py-2 text-xs font-semibold rounded-lg text-slate-400 hover:text-white transition-all';
            render();
        }});

        // ─── Init ───────────────────────────────────────
        updateMetrics();
        render();
    }})();
    </script>
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  ✅ Dashboard compiled: {OUTPUT_FILE} ({len(jobs)} jobs)")


if __name__ == "__main__":
    main()
