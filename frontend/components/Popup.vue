<template>
  <div class="popup-overlay">
    <div class="popup">
      <p class="message">{{ popup.message }}</p>
      <input
        v-if="popup.type === 'prompt'"
        v-model="inputValue"
        class="popup-input"
        autofocus
      />
      <div class="actions">
        <button
          v-if="popup.type !== 'alert'"
          class="btn cancel"
          @click="$emit('cancel')"
        >Annuler</button>
        <button
          class="btn confirm"
          @click="$emit('confirm', inputValue)"
        >OK</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ popup: Object })
const inputValue = ref('')
watch(() => props.popup, p => {
  inputValue.value = p && p.type === 'prompt' ? p.value || '' : ''
})
</script>

<style scoped>
.popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
}
.popup {
  background: var(--color-surface);
  padding: var(--spacing-lg);
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 20px var(--color-shadow);
  width: 90%;
  max-width: 400px;
  text-align: center;
}
.message {
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}
.popup-input {
  width: 100%;
  padding: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  border: 1px solid #ccc;
  border-radius: var(--radius-sm);
}
.actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-md);
}
.btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  background: var(--color-primary);
  color: var(--color-text-primary);
}
.cancel {
  background: var(--color-secondary);
}
</style>
