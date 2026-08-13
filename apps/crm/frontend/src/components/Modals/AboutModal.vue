<template>
  <Dialog v-model:open="show" :size="'sm'">
    <template #body>
      <div class="p-4 pt-5">
        <div class="flex justify-center">
          <div class="flex flex-col items-center">
            <CRMLogo class="mb-3 size-12" />
            <h3 class="text-2xl-semibold text-ink-gray-9">Convect CRM</h3>
          </div>
        </div>
        <hr class="border-t my-3 mx-2" />
        <div>
          <a
            v-for="link in links"
            :key="link.label"
            class="flex py-2 px-2 hover:bg-surface-gray-1 rounded cursor-pointer"
            target="_blank"
            :href="link.url"
          >
            <component
              :is="link.icon"
              v-if="link.icon"
              class="size-4 mr-2 text-ink-gray-7"
            />
            <span class="text-base text-ink-gray-8">
              {{ link.label }}
            </span>
          </a>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import LucideGlobe from '~icons/lucide/globe'
import LucideHeadset from '~icons/lucide/headset'

let show = defineModel({ type: Boolean })

let links = [
  {
    label: __('Website'),
    url: 'https://creativatestudio.my',
    icon: LucideGlobe,
  },
  {
    label: __('Contact Support'),
    url: 'https://wa.me/60177430696',
    icon: LucideHeadset,
  },
]
</script>
