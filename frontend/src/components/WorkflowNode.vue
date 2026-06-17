<template>
  <div 
    :class="['node', node.type ? node.type.split('_')[0] : 'default']"
    @mousedown.stop.prevent="$emit('drag-start', $event, node)"
    @dblclick.stop.prevent="$emit('edit-node', node)"
  >
    <div 
      v-if="!node.type.startsWith('trigger')" 
      class="port in" 
      @mouseup.stop="$emit('port-drop', node.id)" 
      @mouseenter="$emit('port-enter')" 
      @mouseleave="$emit('port-leave')"
    ></div>
    
    <div 
      v-if="!node.type.startsWith('alert')" 
      class="port out" 
      @mousedown.stop.prevent="$emit('port-drag-start', $event, node.id)"
    ></div>
    
    <div class="node-header">
      <span>{{ node.icon }}</span> {{ node.title }}
    </div>
    <div class="node-body" v-html="node.content"></div>
  </div>
</template>

<script setup>
defineProps({
  node: { type: Object, required: true }
})

defineEmits(['drag-start', 'port-drag-start', 'port-drop', 'port-enter', 'port-leave', 'edit-node'])
</script>

<style scoped>
.node {
  position: absolute;
  width: 260px;
  background: var(--bg-card);
  border: 1px solid var(--border-hi);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  cursor: grab;
  user-select: none;
  will-change: left, top, transform; 
}
.node:active { cursor: grabbing; border-color: var(--amber); box-shadow: 0 8px 25px rgba(245, 158, 11, 0.1); }

.node-header {
  padding: 14px; border-bottom: 1px solid var(--border-hi); display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.9rem; border-radius: 12px 12px 0 0; color: var(--text-hi);
}
.node.trigger .node-header { border-top: 4px solid var(--amber); }
.node.action .node-header { border-top: 4px solid var(--blue); }
.node.alert .node-header { border-top: 4px solid var(--red); }

.node-body { padding: 16px; font-size: 0.85rem; color: var(--text-mid); line-height: 1.5; word-wrap: break-word; pointer-events: none; }
.node-body :deep(strong) { color: var(--text-hi); font-weight: bold; }

.port {
  width: 16px; height: 16px; background: var(--bg-card); border: 2px solid var(--border-hi); border-radius: 50%; position: absolute; top: 50%; transform: translateY(-50%); z-index: 11; cursor: crosshair; transition: all 0.2s; pointer-events: auto;
}
.port:hover { transform: translateY(-50%) scale(1.3); background: var(--amber); border-color: #0D1B2A; }
.port.in { left: -8px; }
.port.out { right: -8px; }
.node.trigger .port.out { border-color: var(--amber); }
.node.action .port.out { border-color: var(--blue); }
</style>