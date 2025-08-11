<template>
  <div class="profile">
    <h1>Profil</h1>
    <button @click="$emit('back')">Retour</button>
  </div>
</template>

<script setup>
defineEmits(['back'])
</script>

