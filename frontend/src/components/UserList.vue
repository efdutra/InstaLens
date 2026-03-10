<script setup lang="ts">
import type { User } from '../types/instagram'

defineProps<{
  users: User[]
  title: string
}>()

const getImageUrl = (path: string) => {
  if (!path) return ''
  if (path.startsWith('/images/')) {
    return `http://localhost:8000${path}`
  }
  return path
}
</script>

<template>
  <div class="user-list">
    <div class="user-list__header">
      <h3 class="user-list__title">{{ title }}</h3>
      <span class="user-list__count">{{ users.length }}</span>
    </div>

    <div class="user-list__grid">
      <a
        v-for="user in users"
        :key="user.username"
        :href="user.profile_url"
        target="_blank"
        rel="noopener noreferrer"
        class="user-card"
      >
        <img 
          :src="getImageUrl(user.profile_pic)" 
          :alt="user.username" 
          class="user-card__avatar"
          loading="lazy"
        />
        <div class="user-card__info">
          <p class="user-card__name">{{ user.name || user.username }}</p>
          <p class="user-card__username">@{{ user.username }}</p>
        </div>
      </a>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.user-list {
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  &__title {
    font-size: 1.125rem;
    color: $color-text;
  }

  &__count {
    background: $color-primary;
    color: $color-bg;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    max-height: 400px;
    overflow-y: auto;
    padding: 0.5rem;
    
    @include mobile {
      grid-template-columns: repeat(3, 1fr);
    }

    @include tablet {
      grid-template-columns: repeat(4, 1fr);
    }

    &::-webkit-scrollbar {
      width: 8px;
    }

    &::-webkit-scrollbar-track {
      background: $color-bg;
      border-radius: 4px;
    }

    &::-webkit-scrollbar-thumb {
      background: $color-border;
      border-radius: 4px;

      &:hover {
        background: $color-primary;
      }
    }
  }
}

.user-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: $color-bg;
  border: 1px solid $color-border;
  border-radius: 0.5rem;
  text-decoration: none;
  transition: all 0.2s;

  &:hover {
    border-color: $color-primary;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba($color-primary, 0.2);
  }

  &__avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    border: 2px solid $color-border;
    object-fit: cover;
    margin-bottom: 0.5rem;
  }

  &__info {
    text-align: center;
    width: 100%;
  }

  &__name {
    font-size: 0.875rem;
    font-weight: 600;
    color: $color-text;
    margin-bottom: 0.125rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__username {
    font-size: 0.75rem;
    color: $color-text-muted;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
