<script setup lang="ts">
defineProps<{
  message?: string
}>()
</script>

<template>
  <div class="loading">
    <div class="spinner"></div>
    <p v-if="message" class="loading__message">{{ message }}</p>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 1rem;

  &__message {
    color: $color-text-muted;
    font-size: 0.875rem;
    text-align: center;
  }
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid $color-border;
  border-top-color: $color-primary;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
