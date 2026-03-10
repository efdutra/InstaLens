<script setup lang="ts">
import type { ProfileData } from '../types/instagram'

defineProps<{
  profile: ProfileData
}>()

const getImageUrl = (path: string) => {
  if (!path) return ''
  if (path.startsWith('/images/')) {
    return `http://localhost:8000${path}`
  }
  return path
}

const formatNumber = (num: number) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}
</script>

<template>
  <div class="profile-card card">
    <div class="profile-card__header">
      <img 
        :src="getImageUrl(profile.profile_pic)" 
        :alt="profile.name" 
        class="profile-card__avatar"
        loading="lazy"
      />
      <div class="profile-card__info">
        <h2 class="profile-card__name">{{ profile.name }}</h2>
        <p class="profile-card__username">@{{ profile.username }}</p>
      </div>
    </div>

    <p v-if="profile.bio" class="profile-card__bio">{{ profile.bio }}</p>

    <div class="profile-card__stats">
      <div class="stat">
        <span class="stat__value">{{ formatNumber(profile.posts_count) }}</span>
        <span class="stat__label">Posts</span>
      </div>
      <div class="stat">
        <span class="stat__value">{{ formatNumber(profile.followers_count) }}</span>
        <span class="stat__label">Seguidores</span>
      </div>
      <div class="stat">
        <span class="stat__value">{{ formatNumber(profile.following_count) }}</span>
        <span class="stat__label">Seguindo</span>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.profile-card {
  max-width: 600px;
  margin: 0 auto;

  &__header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  &__avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 2px solid $color-primary;
    object-fit: cover;
  }

  &__info {
    flex: 1;
  }

  &__name {
    font-size: 1.25rem;
    color: $color-text;
    margin-bottom: 0.25rem;
  }

  &__username {
    font-size: 0.875rem;
    color: $color-text-muted;
  }

  &__bio {
    font-size: 0.875rem;
    color: $color-text-muted;
    margin-bottom: 1rem;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    padding-top: 1rem;
    border-top: 1px solid $color-border;
  }
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;

  &__value {
    font-size: 1.25rem;
    font-weight: 700;
    color: $color-primary;
  }

  &__label {
    font-size: 0.75rem;
    color: $color-text-muted;
    margin-top: 0.25rem;
  }
}
</style>
