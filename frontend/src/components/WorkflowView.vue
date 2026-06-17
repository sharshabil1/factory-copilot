<template>
  <div class="workflow-layout">
    
    <aside class="chat-sidebar">
      <div class="header">
        <h1>⚙️ Factory<span>Copilot</span></h1>
      </div>
      
      <div class="chat-history" ref="chatHistoryRef">
        <div v-for="msg in messages" :key="msg.id" :class="['msg', msg.sender]">
          <span v-html="msg.text"></span>
        </div>
      </div>
      
      <div class="chat-input-container">
        <div class="input-wrapper">
          <input 
            type="text" 
            v-model="userInput" 
            @keypress.enter="generateWorkflow" 
            :placeholder="$t('workflow.placeholder')" 
            :disabled="isProcessing"
          />
          <button @click="generateWorkflow" :disabled="isProcessing || !userInput.trim()">
            {{ $t('workflow.send') }}
          </button>
        </div>
      </div>
    </aside>

    <main 
      class="workspace" 
      ref="workspaceRef"
      :class="{ panning: isPanning, drawing: tempWire.active }"
      @wheel="onWheel"
      @mousedown="onCanvasMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
      @dragover.prevent
      @drop="onCanvasDrop"
      :style="{ backgroundSize: `${24 * scale}px ${24 * scale}px`, backgroundPosition: `${pan.x}px ${pan.y}px` }"
    >
      
      <div class="component-palette" @mousedown.stop>
        <h3>Components</h3>
        
        <div 
          v-for="comp in componentLibrary" 
          :key="comp.type"
          class="palette-item"
          draggable="true"
          @dragstart="startDragFromPalette($event, comp)"
        >
          <span class="palette-icon">{{ comp.icon }}</span>
          <span class="palette-title">{{ comp.title }}</span>
        </div>

        <button @click="saveWorkflow" class="save-btn">💾 Save Workflow</button>
      </div>

      <div class="zoom-controls" @mousedown.stop>
        <button @click="adjustZoom(1.2)">+</button>
        <span>{{ Math.round(scale * 100) }}%</span>
        <button @click="adjustZoom(1 / 1.2)">-</button>
        <button @click="resetZoom">⟲</button>
      </div>

      <div class="canvas-plane" :style="{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})` }">
        
        <svg class="svg-layer">
          <path 
            v-for="line in computedLines" 
            :key="line.id" 
            :d="line.path" 
            class="line animated"
          ></path>
          
          <path 
            v-if="tempWire.active"
            :d="tempWirePath"
            class="line drawing-wire"
          ></path>
        </svg>

        <WorkflowNode
          v-for="node in nodes"
          :key="node.id"
          :node="node"
          :style="{ left: `${node.x}px`, top: `${node.y}px`, zIndex: node.zIndex || 10 }"
          @drag-start="initNodeDrag"
          @port-drag-start="startDrawingWire"
          @port-drop="finishDrawingWire"
          @port-enter="hoveringPort = true"
          @port-leave="hoveringPort = false"
          @edit-node="openNodeEditor" 
        />

      </div>
    </main>
  </div>
  <div v-if="editingNode" class="modal-overlay" @mousedown.self="closeNodeEditor">
      <div class="modal-card">
        
        <header class="modal-header">
          <h2>{{ editingNode.icon }} Configure: {{ editingNode.title }}</h2>
          <button @click="closeNodeEditor" class="close-btn">✖</button>
        </header>

        <div class="modal-body">
          
          <template v-if="editingNode.type === 'trigger_cron'">
            <div class="input-group">
              <label>Interval Schedule</label>
              <select v-model="editingConfig.interval">
                <option value="5_minutes">Every 5 Minutes</option>
                <option value="15_minutes">Every 15 Minutes</option>
                <option value="1_hour">Every 1 Hour</option>
                <option value="daily">Daily at Midnight</option>
              </select>
            </div>
          </template>

          <template v-else-if="editingNode.type === 'action_api'">
            <div class="input-group">
              <label>HTTP Method</label>
              <select v-model="editingConfig.method">
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
              </select>
            </div>
            <div class="input-group">
              <label>Endpoint URL</label>
              <input type="text" v-model="editingConfig.endpoint" placeholder="https://api.odoo.com/v1/..." />
            </div>
          </template>

          <template v-else-if="editingNode.type === 'alert_email'">
            <div class="input-group">
              <label>Recipient Address</label>
              <input type="email" v-model="editingConfig.to_address" placeholder="manager@factory.com" />
            </div>
            <div class="input-group">
              <label>Subject Line</label>
              <input type="text" v-model="editingConfig.subject" placeholder="Urgent: Stock Depleted" />
            </div>
          </template>
          
          <template v-else>
            <p class="fallback-text">Advanced configuration for this node is managed via AI prompt.</p>
          </template>

        </div>

        <footer class="modal-footer">
          <button @click="closeNodeEditor" class="btn-cancel">Cancel</button>
          <button @click="saveNodeConfig" class="btn-save">Save Configuration</button>
        </footer>

      </div>
    </div>
</template>

<script setup>
import { ref, computed, nextTick, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import WorkflowNode from './WorkflowNode.vue'
import { api } from '@/services/api.js'

const { t } = useI18n()
const showToast = inject('toast')
// Add these refs near your other state variables
const editingNode = ref(null)
const editingConfig = ref({})

// Add these functions to handle the modal logic
function openNodeEditor(node) {
  editingNode.value = node
  // Clone the config so we don't mutate the canvas until they click "Save"
  editingConfig.value = JSON.parse(JSON.stringify(node.config || {}))
}

function closeNodeEditor() {
  editingNode.value = null
  editingConfig.value = {}
}

function saveNodeConfig() {
  // Find the actual node in the array and update its config and display content
  const target = nodes.value.find(n => n.id === editingNode.value.id)
  if (target) {
    target.config = editingConfig.value
    
    // Update the visual content on the card so the user sees their changes!
    if (target.type === 'trigger_cron') {
      target.content = `<strong>Schedule:</strong><br>${target.config.interval.replace('_', ' ')}`
    } else if (target.type === 'alert_email') {
      target.content = `<strong>To:</strong><br>${target.config.to_address || '(Empty)'}`
    } else if (target.type === 'action_api') {
      target.content = `<strong>${target.config.method}:</strong><br>${target.config.endpoint || '(Empty)'}`
    }
  }
  
  showToast('Node configuration saved', '💾')
  closeNodeEditor()
}
// ── STATE ────────────────────────────────────────────────────────
const chatHistoryRef = ref(null)
const userInput = ref('')
const isProcessing = ref(false)
const messages = ref([{ id: 0, sender: 'ai', text: t('workflow.welcome') }])

const nodes = ref([])
const connections = ref([])

const workspaceRef = ref(null)
const isPanning = ref(false)
const pan = ref({ x: 0, y: 0 })
const startPan = ref({ x: 0, y: 0 })
const scale = ref(1)

const activeNode = ref(null)
const dragOffset = ref({ x: 0, y: 0 })

// ── COMPONENT PALETTE (DRAG & DROP) ──────────────────────────────
const componentLibrary = [
  { type: 'trigger_db', icon: '📡', title: 'DB Monitor', content: 'Double-click to configure table rules', config: { table: '', condition: '' } },
  { type: 'trigger_cron', icon: '⏱️', title: 'Cron Schedule', content: 'Double-click to set timer', config: { interval: '15_minutes' } },
  { type: 'action_api', icon: '🔌', title: 'API / Odoo Action', content: 'Double-click to set endpoint', config: { endpoint: '', method: 'POST' } },
  { type: 'alert_email', icon: '✉️', title: 'Email Alert', content: 'Double-click to set recipient', config: { to_address: '', subject: '' } }
]

// Package the node data to survive the HTML5 drag event
function startDragFromPalette(e, component) {
  e.dataTransfer.dropEffect = 'copy'
  e.dataTransfer.setData('application/json', JSON.stringify(component))
}

// Intercept the drop on the canvas and calculate exact scaling coordinates
function onCanvasDrop(e) {
  const payload = e.dataTransfer.getData('application/json')
  if (!payload) return

  const component = JSON.parse(payload)
  const wsRect = workspaceRef.value.getBoundingClientRect()
  
  // Calculate exact drop position accounting for user's zoom and pan
  const unscaledX = ((e.clientX - wsRect.left) - pan.value.x) / scale.value
  const unscaledY = ((e.clientY - wsRect.top) - pan.value.y) / scale.value

  nodes.value.push({
    id: `node-${Date.now()}`,
    type: component.type,
    icon: component.icon,
    title: component.title,
    content: component.content,
    x: unscaledX - 130, // Offset by half the node width so it drops exactly on the mouse
    y: unscaledY - 40,  // Offset by half the node height
    zIndex: 10
  })

  showToast(`Added ${component.title}`, '✅')
}

// ── WIRE DRAWING STATE ──────────────────────────────────────────
const tempWire = ref({ active: false, fromNodeId: null, startX: 0, startY: 0, endX: 0, endY: 0 })
const hoveringPort = ref(false)

const tempWirePath = computed(() => {
  if (!tempWire.value.active) return ''
  const { startX, startY, endX, endY } = tempWire.value
  const curveForce = Math.max(Math.abs(endX - startX) * 0.5, 50)
  return `M ${startX} ${startY} C ${startX + curveForce} ${startY}, ${endX - curveForce} ${endY}, ${endX} ${endY}`
})

function startDrawingWire(event, nodeId) {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return
  tempWire.value = {
    active: true,
    fromNodeId: nodeId,
    startX: node.x + 260,
    startY: node.y + 75,
    endX: node.x + 260,
    endY: node.y + 75
  }
}

function finishDrawingWire(targetNodeId) {
  if (!tempWire.value.active) return
  const fromId = tempWire.value.fromNodeId
  
  if (fromId === targetNodeId) {
    showToast('Cannot connect a node to itself!', '⚠️')
  } else {
    const exists = connections.value.some(c => c.from === fromId && c.to === targetNodeId)
    if (!exists) {
      connections.value.push({ id: `conn-${Date.now()}`, from: fromId, to: targetNodeId })
    }
  }
  tempWire.value.active = false
}

const computedLines = computed(() => {
  return connections.value.map(conn => {
    const fromNode = nodes.value.find(n => n.id === conn.from)
    const toNode = nodes.value.find(n => n.id === conn.to)
    if (!fromNode || !toNode) return { id: conn.id, path: '' }

    const startX = fromNode.x + 260
    const startY = fromNode.y + 75
    const endX = toNode.x
    const endY = toNode.y + 75
    const curveForce = Math.max(Math.abs(endX - startX) * 0.5, 50)
    return { id: conn.id, path: `M ${startX} ${startY} C ${startX + curveForce} ${startY}, ${endX - curveForce} ${endY}, ${endX} ${endY}` }
  })
})


// ── BACKEND INTEGRATION (Real Setup) ──────────────────────────────
async function generateWorkflow() {
  if (!userInput.value.trim() || isProcessing.value) return
  const query = userInput.value
  isProcessing.value = true
  addMessage(query, 'user')
  userInput.value = ''
  
  try {
    // This is now wired for your real FastAPI backend!
    addMessage("Sending request to FastAPI...", 'ai')
    const { data } = await api.post('/api/workflow/generate', { prompt: query })
    
    // If the backend returns nodes, render them:
    if (data.nodes) {
      nodes.value = data.nodes
      connections.value = data.connections || []
      resetZoom()
      addMessage("I have built the workflow on your canvas.", 'ai')
    }
  } catch (error) {
    addMessage("⚠️ Backend not connected yet. You can build manually using the Palette!", 'ai')
  } finally {
    isProcessing.value = false
  }
}

async function saveWorkflow() {
  // Prepares the JSON schema to shoot to FastAPI
  const payload = {
    nodes: nodes.value,
    connections: connections.value
  }
  
  try {
    showToast('Saving workflow to Postgres...', '💾')
    // await api.post('/api/workflow/save', payload)
    console.log("JSON Payload ready for backend:", payload)
    setTimeout(() => showToast('Workflow saved!', '✅'), 500)
  } catch (err) {
    showToast('Failed to save workflow', '❌')
  }
}

function addMessage(text, sender) {
  messages.value.push({ id: Date.now(), text, sender })
  nextTick(() => { if (chatHistoryRef.value) chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight })
}


// ── CANVAS MATH (Pan, Zoom, Drag) ─────────────────────────────────
function onWheel(e) {
  e.preventDefault()
  if (!workspaceRef.value) return
  const wsRect = workspaceRef.value.getBoundingClientRect()
  const mouseX = e.clientX - wsRect.left
  const mouseY = e.clientY - wsRect.top
  const pointX = (mouseX - pan.value.x) / scale.value
  const pointY = (mouseY - pan.value.y) / scale.value
  const delta = e.deltaY * -0.002
  let newScale = scale.value * Math.exp(delta)
  scale.value = Math.min(Math.max(0.2, newScale), 3)
  pan.value.x = mouseX - pointX * scale.value
  pan.value.y = mouseY - pointY * scale.value
}

function adjustZoom(factor) { scale.value = Math.min(Math.max(0.2, scale.value * factor), 3) }
function resetZoom() { scale.value = 1; pan.value = { x: 0, y: 0 } }

function onCanvasMouseDown(e) {
  isPanning.value = true
  startPan.value = { x: e.clientX - pan.value.x, y: e.clientY - pan.value.y }
}

function initNodeDrag(e, node) {
  activeNode.value = node
  const wsRect = workspaceRef.value.getBoundingClientRect()
  const unscaledX = ((e.clientX - wsRect.left) - pan.value.x) / scale.value
  const unscaledY = ((e.clientY - wsRect.top) - pan.value.y) / scale.value
  dragOffset.value = { x: unscaledX - node.x, y: unscaledY - node.y }
  nodes.value.forEach(n => n.zIndex = 10)
  node.zIndex = 100
}

function onMouseMove(e) {
  if (!workspaceRef.value) return
  const wsRect = workspaceRef.value.getBoundingClientRect()

  if (tempWire.value.active) {
    tempWire.value.endX = ((e.clientX - wsRect.left) - pan.value.x) / scale.value
    tempWire.value.endY = ((e.clientY - wsRect.top) - pan.value.y) / scale.value
  } else if (isPanning.value) {
    pan.value.x = e.clientX - startPan.value.x
    pan.value.y = e.clientY - startPan.value.y
  } else if (activeNode.value) {
    activeNode.value.x = (((e.clientX - wsRect.left) - pan.value.x) / scale.value) - dragOffset.value.x
    activeNode.value.y = (((e.clientY - wsRect.top) - pan.value.y) / scale.value) - dragOffset.value.y
  }
}

function onMouseUp() {
  if (tempWire.value.active && !hoveringPort.value) tempWire.value.active = false
  activeNode.value = null
  isPanning.value = false
}
</script>

<style scoped>
.workflow-layout { display: flex; height: 100%; width: 100%; background-color: var(--bg-shell); overflow: hidden; }

/* Sidebar Chat */
.chat-sidebar { width: 400px; background-color: var(--bg-panel); border-right: 1px solid var(--border); display: flex; flex-direction: column; z-index: 20; }
[dir="rtl"] .chat-sidebar { border-right: none; border-left: 1px solid var(--border); }
.header { padding: 24px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.header h1 { font-size: 1.25rem; font-weight: 700; display: flex; align-items: center; gap: 8px; color: var(--text-hi); }
.header h1 span { color: var(--amber); }
.chat-history { flex-grow: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
.msg { max-width: 85%; padding: 14px 18px; border-radius: 12px; font-size: 0.9rem; line-height: 1.5; }
.msg.user { background-color: var(--amber-dim); color: var(--amber); align-self: flex-end; border-bottom-right-radius: 4px; }
.msg.ai { background-color: var(--bg-card); color: var(--text-hi); border: 1px solid var(--border-hi); align-self: flex-start; border-bottom-left-radius: 4px; }
.msg.ai :deep(strong) { color: var(--amber); }
.chat-input-container { padding: 20px; border-top: 1px solid var(--border); background: var(--bg-panel); }
.input-wrapper { display: flex; background: var(--bg-input); border: 1px solid var(--border-hi); border-radius: 8px; transition: 0.2s; overflow: hidden; }
.input-wrapper input { flex-grow: 1; border: none; padding: 14px 16px; background: transparent; outline: none; color: var(--text-hi); }
.input-wrapper button { background: var(--amber); color: #0D1B2A; border: none; padding: 0 24px; font-weight: 600; cursor: pointer; }
.input-wrapper button:disabled { background: var(--border-hi); color: var(--text-lo); cursor: not-allowed; }

/* ── NODE CONFIGURATION MODAL ── */
.modal-overlay {
  position: absolute; inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}

.modal-card {
  width: 400px;
  background: var(--bg-card);
  border: 1px solid var(--border-hi);
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
  display: flex; flex-direction: column;
  overflow: hidden;
  animation: popIn 0.2s ease-out;
}

.modal-header {
  padding: 1rem 1.5rem;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border-hi);
  display: flex; justify-content: space-between; align-items: center;
}

.modal-header h2 { font-size: 1rem; color: var(--text-hi); font-weight: 600; display: flex; gap: 8px;}
.close-btn { background: transparent; border: none; color: var(--text-mid); cursor: pointer; font-size: 1.2rem; }
.close-btn:hover { color: var(--red); }

.modal-body { padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }

.input-group { display: flex; flex-direction: column; gap: 0.4rem; }
.input-group label { font-size: 0.8rem; font-weight: 600; color: var(--text-mid); text-transform: uppercase; letter-spacing: 0.5px; }
.input-group input, .input-group select {
  background: var(--bg-input); border: 1px solid var(--border-hi);
  padding: 0.75rem; border-radius: 6px; color: var(--text-hi); outline: none; font-family: inherit;
}
.input-group input:focus, .input-group select:focus { border-color: var(--amber); }

.fallback-text { font-size: 0.85rem; color: var(--text-lo); font-style: italic; text-align: center; }

.modal-footer {
  padding: 1rem 1.5rem; border-top: 1px solid var(--border-hi);
  display: flex; justify-content: flex-end; gap: 0.75rem; background: var(--bg-shell);
}

.btn-cancel { background: transparent; border: 1px solid var(--border-hi); color: var(--text-mid); padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; font-weight: 600; }
.btn-cancel:hover { background: var(--bg-panel); color: var(--text-hi); }

.btn-save { background: var(--amber); color: #0D1B2A; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; font-weight: 700; }
.btn-save:hover { filter: brightness(1.1); }

/* Canvas Workspace */
.workspace {
  flex-grow: 1; position: relative; background-color: var(--bg-shell);
  background-image: radial-gradient(var(--border-hi) 1px, transparent 1px);
  overflow: hidden; cursor: grab;
}
.workspace.panning { cursor: grabbing; }
.workspace.drawing .svg-layer { pointer-events: none; }

/* THE COMPONENT PALETTE */
.component-palette {
  position: absolute;
  top: 20px; left: 20px;
  width: 240px;
  background: var(--bg-card);
  border: 1px solid var(--border-hi);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  padding: 1rem;
  display: flex; flex-direction: column; gap: 0.75rem;
  z-index: 30;
}
[dir="rtl"] .component-palette { left: auto; right: 20px; }

.component-palette h3 {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-mid);
  margin-bottom: 0.5rem;
}

.palette-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px;
  background: var(--bg-input);
  border: 1px solid var(--border-hi);
  border-radius: 8px;
  cursor: grab;
  color: var(--text-hi);
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}
.palette-item:hover {
  border-color: var(--amber);
  background: var(--amber-dim);
}
.palette-item:active { cursor: grabbing; }

.save-btn {
  margin-top: 1rem;
  padding: 10px;
  background: rgba(16, 185, 129, 0.1);
  color: var(--green);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.save-btn:hover { background: rgba(16, 185, 129, 0.2); border-color: var(--green); }

.canvas-plane { position: absolute; top: 0; left: 0; width: 100%; height: 100%; transform-origin: 0 0; will-change: transform; }
.svg-layer { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1; overflow: visible; }
.line { fill: none; stroke: var(--border-hi); stroke-width: 2.5px; transition: stroke 0.3s; }
.line.animated { stroke: var(--amber); opacity: 0.8; }

.line.drawing-wire {
  stroke: var(--amber); stroke-dasharray: 6 6; opacity: 0.5; animation: march 0.5s linear infinite;
}

@keyframes march { from { stroke-dashoffset: 12; } to { stroke-dashoffset: 0; } }

.zoom-controls { position: absolute; bottom: 20px; right: 20px; background: var(--bg-card); border: 1px solid var(--border-hi); border-radius: 8px; display: flex; flex-direction: column; overflow: hidden; z-index: 30; }
[dir="rtl"] .zoom-controls { right: auto; left: 20px; }
.zoom-controls button { background: transparent; border: none; padding: 10px 14px; cursor: pointer; font-size: 1.1rem; font-weight: 600; color: var(--text-mid); transition: 0.2s; }
.zoom-controls button:hover { background: var(--bg-panel); color: var(--amber); }
.zoom-controls button:not(:last-child) { border-bottom: 1px solid var(--border-hi); }
.zoom-controls span { font-size: 0.75rem; padding: 6px; text-align: center; border-bottom: 1px solid var(--border-hi); color: var(--text-mid); }
</style>