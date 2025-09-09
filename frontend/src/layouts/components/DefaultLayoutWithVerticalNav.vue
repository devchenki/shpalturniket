<script lang="ts" setup>
import navItems from '@/navigation/vertical'
import { themeConfig } from '@themeConfig'

// Components - убраны неиспользуемые компоненты

// @layouts plugin
import { VerticalNavLayout } from '@layouts'
</script>

<template>
  <VerticalNavLayout :nav-items="navItems">
    <!-- 👉 navbar - убран по запросу пользователя -->

    <!-- 👉 Pages -->
    <slot />

    <!-- 👉 Footer - убран по запросу пользователя -->

    <!-- 👉 Customizer - убран по запросу пользователя -->
  </VerticalNavLayout>
</template>
