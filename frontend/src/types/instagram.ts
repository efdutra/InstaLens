export interface ProfileData {
  username: string
  name: string
  bio?: string
  profile_pic: string
  posts_count: number
  followers_count: number
  following_count: number
}

export interface User {
  username: string
  name?: string
  profile_url: string
  profile_pic: string
}

export interface ScrapeRequest {
  username: string
  max_followers?: number
  max_following?: number
  get_followers: boolean
  get_following: boolean
}

export interface ScrapeResponse {
  profile: ProfileData
  followers: User[]
  following: User[]
}

export interface ApiError {
  detail: string
  status?: number
}
