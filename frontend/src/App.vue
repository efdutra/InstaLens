<script setup lang="ts">
import HomePage from './components/HomePage.vue'
</script>

<template>
  <div class="app">
    <main class="main">
      <div class="container">
        <HomePage />
      </div>
    </main>
  </div>
</template>

<style scoped lang="scss">
@use './styles/variables' as *;

.app {
  min-height: 100vh;
}

.main {
  padding: 2rem 0;

  @include tablet {
    padding: 3rem 0;
  }
}
</style>
