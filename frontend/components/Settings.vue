<template>
  <div class="settings">
    <h1>Paramètres</h1>
    <button @click="$emit('back')">Retour</button>
  </div>
</template>

<script setup>
defineEmits(['back'])
</script>

