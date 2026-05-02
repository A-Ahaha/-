import type { Router } from "vue-router";
import { useUserStore } from "@/stores/user";
import { getAdminAppUrl } from "@/api/env";

function getMetaRole(meta: unknown): string | undefined {
  if (!meta || typeof meta !== "object") return undefined;
  const role = (meta as Record<string, unknown>).role;
  if (typeof role === "string") return role;
  return undefined;
}

function isPublicRoute(meta: unknown): boolean {
  if (!meta || typeof meta !== "object") return false;
  return Boolean((meta as Record<string, unknown>).public);
}

function requiresAuth(meta: unknown): boolean {
  if (!meta || typeof meta !== "object") return false;
  return Boolean((meta as Record<string, unknown>).requiresAuth);
}

function getTitle(meta: unknown): string | undefined {
  if (!meta || typeof meta !== "object") return undefined;
  const title = (meta as Record<string, unknown>).title;
  if (typeof title === "string") return title;
  return undefined;
}

export function setupRouterGuards(router: Router) {
  router.beforeEach((to) => {
    const userStore = useUserStore();

    if (isPublicRoute(to.meta)) {
      if (
        to.path === "/login" &&
        userStore.isLoggedIn &&
        userStore.role === "user"
      ) {
        return { path: "/home", replace: true };
      }
      return true;
    }

    if (requiresAuth(to.meta) && !userStore.isLoggedIn) {
      return { path: "/login", query: { redirect: to.fullPath } };
    }

    const requiredRole = getMetaRole(to.meta);
    if (requiredRole && userStore.role !== requiredRole) {
      if (userStore.role === "admin") {
        const adminUrl = getAdminAppUrl();
        if (adminUrl) {
          const base = adminUrl.endsWith("/")
            ? adminUrl.slice(0, -1)
            : adminUrl;
          window.location.href = `${base}/admin`;
          return false;
        }
      }
      return { path: "/403", replace: true };
    }

    return true;
  });

  router.afterEach((to) => {
    const pageTitle = getTitle(to.meta);
    document.title = pageTitle
      ? `${pageTitle} · 商品质量溯源系统 · 用户端`
      : "商品质量溯源系统 · 用户端";
  });
}
