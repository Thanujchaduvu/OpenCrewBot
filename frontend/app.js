let currentTab = 'rooms';

function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
  document.getElementById(`tab-${tab}`).classList.remove('hidden');
  document.querySelectorAll('.nav-btn').forEach(b => {
    const active = b.dataset.tab === tab;
    b.className = active
      ? 'nav-btn active text-left px-3 py-2.5 rounded-lg text-sm font-medium bg-indigo-50 text-indigo-700 flex justify-between items-center'
      : 'nav-btn text-left px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100 flex justify-between items-center';
  });
  refreshAll();
}

function fillPrompt(roomId, text) {
  document.getElementById('room-select').value = roomId;
  document.getElementById('instruction-input').value = text;
  loadRoomDetails();
}

async function dispatchInstruction() {
  const room_id = document.getElementById('room-select').value;
  const instruction = document.getElementById('instruction-input').value.trim();
  if (!instruction) return;
  document.getElementById('instruction-input').value = '';
  await fetch('/api/runs', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ room_id, instruction })
  });
  setTimeout(refreshAll, 350);
}

async function interruptRun(runId) {
  const newInst = prompt('Enter live mid-run interruption / updated requirement:');
  if (!newInst) return;
  await fetch(`/api/runs/${runId}/interrupt`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ instruction: newInst })
  });
  setTimeout(refreshAll, 350);
}

async function resolveApproval(approvalId, decision) {
  await fetch(`/api/approvals/${approvalId}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ decision })
  });
  setTimeout(refreshAll, 350);
}

async function createDynamicAgent() {
  const prompt = document.getElementById('nl-agent-input').value.trim();
  if (!prompt) return;
  document.getElementById('nl-agent-input').value = '';
  await fetch('/api/agents/dynamic', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ prompt })
  });
  refreshAll();
}

async function loadSelectedMemory() {
  const val = document.getElementById('memory-select').value;
  if (!val) return;
  const [scope, entityId] = val.split('/');
  const res = await (await fetch(`/api/memory/${scope}/${entityId}`)).json();
  document.getElementById('memory-editor').value = res.content;
}

async function saveSelectedMemory() {
  const val = document.getElementById('memory-select').value;
  if (!val) return;
  const [scope, entityId] = val.split('/');
  const content = document.getElementById('memory-editor').value;
  await fetch(`/api/memory/${scope}/${entityId}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ content })
  });
  alert('Markdown memory saved to disk! Agents will read this updated file on their next turn.');
}

async function toggleWorkflow(id) {
  await fetch(`/api/workflows/${id}/toggle`, { method: 'POST' });
  refreshAll();
}

async function runWorkflowNow(id) {
  await fetch(`/api/workflows/${id}/run`, { method: 'POST' });
  switchTab('rooms');
}

async function loadRoomDetails() {
  const roomId = document.getElementById('room-select').value;
  if (!roomId) return;
  const room = await (await fetch(`/api/rooms/${roomId}`)).json();
  const feed = document.getElementById('room-feed');
  feed.innerHTML = room.messages.slice().reverse().map(m => {
    const badgeColor = m.msg_type === 'DELIVERABLE' ? 'bg-emerald-100 text-emerald-800'
      : m.msg_type === 'PLAN' ? 'bg-indigo-100 text-indigo-800'
      : m.msg_type === 'USER' ? 'bg-slate-200 text-slate-800'
      : 'bg-sky-100 text-sky-800';
    return `
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="font-bold text-sm text-slate-900">${m.sender}</span>
            <span class="text-xs px-2 py-0.5 rounded font-semibold ${badgeColor}">${m.msg_type}</span>
          </div>
          <span class="text-xs text-slate-400">${m.timestamp}</span>
        </div>
        <pre class="whitespace-pre-wrap font-sans text-sm text-slate-700 leading-relaxed">${m.content}</pre>
      </div>
    `;
  }).join('') || '<p class="text-sm text-slate-400">No messages in this room yet. Launch an instruction above.</p>';
}

async function refreshAll() {
  const status = await (await fetch('/api/system/status')).json();
  document.getElementById('status-badges').innerHTML = `
    <span class="px-2.5 py-1 rounded-full ${status.mock_mode ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}">
      Mode: ${status.mock_mode ? 'SIMULATED / MOCK' : 'LIVE APIs'}
    </span>
    <span class="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">Agents: ${status.agents_count}</span>
    <span class="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">Skills: ${status.skills_count}</span>
  `;
  const pill = document.getElementById('approval-pill');
  if (status.pending_approvals > 0) {
    pill.textContent = status.pending_approvals;
    pill.classList.remove('hidden');
  } else {
    pill.classList.add('hidden');
  }

  // Populate rooms dropdown
  const rooms = await (await fetch('/api/rooms')).json();
  const roomSel = document.getElementById('room-select');
  const prevRoom = roomSel.value;
  roomSel.innerHTML = rooms.map(r => `<option value="${r.id}">${r.name}</option>`).join('');
  if (prevRoom) roomSel.value = prevRoom;
  await loadRoomDetails();

  // Runs & DAG
  const runs = await (await fetch('/api/runs')).json();
  document.getElementById('runs-container').innerHTML = runs.map(r => `
    <div class="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <span class="text-xs font-mono text-slate-400">${r.run_id} &bull; ${r.room_id}</span>
          <h3 class="font-bold text-sm text-slate-900">${r.instruction}</h3>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-800">${r.status}</span>
          <button onclick="interruptRun('${r.run_id}')" class="text-xs bg-amber-500 hover:bg-amber-600 text-white px-3 py-1 rounded-lg font-semibold">Interrupt & Adapt</button>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
        ${r.tasks.map(t => `
          <div class="p-3 rounded-lg border ${t.status === 'COMPLETED' ? 'border-emerald-200 bg-emerald-50/40' : t.status === 'AWAITING_APPROVAL' ? 'border-amber-300 bg-amber-50' : t.status === 'FAILED' ? 'border-rose-300 bg-rose-50' : 'border-slate-200 bg-slate-50'}">
            <div class="flex justify-between text-xs font-bold mb-1">
              <span>${t.task_id}</span>
              <span>${t.status}</span>
            </div>
            <div class="text-xs font-semibold text-slate-800">${t.title}</div>
            <div class="text-[11px] text-slate-500 mt-1">Agent: ${t.assigned_agent} | Deps: ${t.dependencies.join(', ') || 'None'}</div>
            ${t.error ? `<div class="text-[11px] text-rose-700 font-semibold mt-1">${t.error}</div>` : ''}
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');

  // Approvals & Audit
  const approvals = await (await fetch('/api/approvals')).json();
  document.getElementById('approvals-list').innerHTML = approvals.slice().reverse().map(a => `
    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
      <div class="space-y-1">
        <div class="flex items-center gap-2">
          <span class="font-bold text-sm">${a.tool_name}</span>
          <span class="text-xs px-2 py-0.5 rounded bg-slate-100 font-mono">${a.permission_level}</span>
          <span class="text-xs px-2 py-0.5 rounded font-bold ${a.status === 'PENDING' ? 'bg-amber-100 text-amber-800' : a.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">${a.status}</span>
        </div>
        <p class="text-xs text-slate-600">Agent: <b>${a.agent_id}</b> | Run: <code>${a.run_id}</code></p>
        <pre class="text-xs bg-slate-50 p-2 rounded border border-slate-200">${JSON.stringify(a.action_preview, null, 2)}</pre>
      </div>
      ${a.status === 'PENDING' ? `
        <div class="flex gap-2">
          <button onclick="resolveApproval('${a.approval_id}', 'APPROVED')" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold">Approve</button>
          <button onclick="resolveApproval('${a.approval_id}', 'REJECTED')" class="bg-rose-600 hover:bg-rose-700 text-white px-4 py-2 rounded-lg text-xs font-bold">Reject Action</button>
        </div>
      ` : ''}
    </div>
  `).join('') || '<p class="text-sm text-slate-400">No approval requests recorded yet.</p>';

  const audits = await (await fetch('/api/audit')).json();
  document.getElementById('audit-list').innerHTML = audits.slice().reverse().map(l =>
    `<div class="p-2 bg-slate-50 rounded border border-slate-200">[${l.timestamp}] <b>${l.event_type}</b> — ${JSON.stringify(l)}</div>`
  ).join('');

  // Agents
  const agents = await (await fetch('/api/agents')).json();
  document.getElementById('agents-grid').innerHTML = agents.map(a => `
    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-2">
      <div class="flex justify-between items-start">
        <div>
          <h3 class="font-bold text-sm text-slate-900">${a.name}</h3>
          <p class="text-xs text-indigo-600 font-medium">${a.role}</p>
        </div>
        <span class="text-[11px] font-bold px-2 py-0.5 rounded bg-slate-100">${a.permission_level}</span>
      </div>
      <p class="text-xs text-slate-600">${a.persona}</p>
      <div class="text-[11px] text-slate-500">Model: <b>${a.model_config_data.provider}/${a.model_config_data.primary_model}</b></div>
      <div class="text-[11px] text-slate-500">Skills: ${a.skills.join(', ')}</div>
    </div>
  `).join('');

  // Memory Dropdown
  const mems = await (await fetch('/api/memory')).json();
  const memSel = document.getElementById('memory-select');
  const prevMem = memSel.value;
  memSel.innerHTML = mems.map(m => `<option value="${m.scope}/${m.entity_id}">${m.filename}</option>`).join('');
  if (prevMem) memSel.value = prevMem;
  if (!document.getElementById('memory-editor').value) await loadSelectedMemory();

  // Integrations & Skills
  const ints = await (await fetch('/api/integrations')).json();
  document.getElementById('integrations-grid').innerHTML = ints.map(i => `
    <div class="p-3 rounded-lg border border-slate-200 bg-slate-50">
      <div class="flex justify-between items-center mb-1">
        <span class="font-bold text-xs">${i.name}</span>
        <span class="text-[10px] font-bold px-2 py-0.5 rounded ${i.mode.startsWith('LIVE') ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">${i.mode}</span>
      </div>
      <div class="text-[11px] text-slate-500">Tools: ${i.capabilities.join(', ')}</div>
    </div>
  `).join('');

  const skills = await (await fetch('/api/skills')).json();
  document.getElementById('skills-grid').innerHTML = skills.map(s => `
    <div class="p-3 rounded-lg border border-slate-200">
      <h4 class="font-bold text-xs text-indigo-700 mb-1">${s.name} (<code>${s.filename}</code>)</h4>
      <pre class="whitespace-pre-wrap text-[11px] text-slate-600 font-sans">${s.content}</pre>
    </div>
  `).join('');

  // Workflows
  const wfs = await (await fetch('/api/workflows')).json();
  document.getElementById('workflows-list').innerHTML = wfs.map(w => `
    <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2">
          <h3 class="font-bold text-sm">${w.name}</h3>
          <span class="text-xs px-2 py-0.5 rounded font-bold ${w.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'}">${w.status}</span>
          <span class="text-xs font-mono text-slate-500">Cron: ${w.cron_schedule}</span>
        </div>
        <p class="text-xs text-slate-600 mt-1">${w.description}</p>
        <p class="text-[11px] text-slate-400 mt-1">Runs executed: ${w.run_history.length} | Last run: ${w.last_run_at || 'Never'}</p>
      </div>
      <div class="flex gap-2">
        <button onclick="runWorkflowNow('${w.workflow_id}')" class="bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold">Run Now</button>
        <button onclick="toggleWorkflow('${w.workflow_id}')" class="bg-slate-200 text-slate-800 px-3 py-1.5 rounded-lg text-xs font-semibold">${w.status === 'ACTIVE' ? 'Pause' : 'Resume'}</button>
      </div>
    </div>
  `).join('');

  // Usage Ledger
  const usage = await (await fetch('/api/models/usage')).json();
  document.getElementById('usage-kpis').innerHTML = `
    <div class="p-3 bg-slate-50 rounded-lg border border-slate-200"><div class="text-xs text-slate-500">Total LLM Calls</div><div class="text-lg font-bold">${usage.total_calls}</div></div>
    <div class="p-3 bg-slate-50 rounded-lg border border-slate-200"><div class="text-xs text-slate-500">Total Tokens</div><div class="text-lg font-bold">${usage.total_tokens}</div></div>
    <div class="p-3 bg-slate-50 rounded-lg border border-slate-200"><div class="text-xs text-slate-500">Estimated Cost (USD)</div><div class="text-lg font-bold">$${usage.total_cost_usd}</div></div>
  `;
  document.getElementById('usage-logs').innerHTML = usage.recent_calls.slice().reverse().map(c =>
    `<div class="p-2 bg-slate-50 rounded border border-slate-200">[${c.timestamp}] <b>${c.provider}/${c.model}</b> (${c.execution_mode}) — ${c.prompt_tokens + c.completion_tokens} tokens ($${c.estimated_cost_usd})</div>`
  ).join('');
}

refreshAll();
setInterval(() => {
  if (currentTab === 'rooms' || currentTab === 'tasks' || currentTab === 'approvals') {
    refreshAll();
  }
}, 4000);
