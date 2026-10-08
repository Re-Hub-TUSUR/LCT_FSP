import type { ComponentType } from 'react'
import type { RouteObject } from 'react-router'
import type { UserRole } from '@/entities/user'
import { ROUTES } from '@/shared/config'
import { Splash } from '@/shared/ui'
import { MainLayout } from '../layouts/main-layout'
import { RootLayout } from '../layouts/root-layout'
import { RequireAuth } from './guards'
import { RouteError } from './route-error'

type Access = { auth: true; roles?: readonly UserRole[] }

/** Every page is a separate chunk loaded on navigation; protected ones are wrapped in a guard. */
function lazyPage(load: () => Promise<ComponentType>, access?: Access): RouteObject['lazy'] {
  return async () => {
    const Page = await load()
    if (!access) return { Component: Page }
    return {
      Component: function GuardedPage() {
        return (
          <RequireAuth roles={access.roles}>
            <Page />
          </RequireAuth>
        )
      },
    }
  }
}

const authRequired: Access = { auth: true }

export const routes: RouteObject[] = [
  {
    element: <RootLayout />,
    errorElement: <RouteError />,
    hydrateFallbackElement: <Splash />,
    children: [
      {
        path: ROUTES.landing,
        lazy: lazyPage(() => import('@/pages/landing').then((m) => m.LandingPage)),
      },
      {
        element: <MainLayout />,
        children: [
          {
            path: ROUTES.auth,
            lazy: lazyPage(() => import('@/pages/auth').then((m) => m.AuthPage)),
          },
          {
            path: ROUTES.employerAuth,
            lazy: lazyPage(() => import('@/pages/auth').then((m) => m.EmployerAuthPage)),
          },
          {
            path: ROUTES.candidateAuth,
            lazy: lazyPage(() => import('@/pages/auth').then((m) => m.CandidateAuthPage)),
          },
          {
            path: ROUTES.vacancies,
            lazy: lazyPage(() => import('@/pages/vacancies').then((m) => m.VacanciesPage)),
          },
          {
            path: ROUTES.vacancyNew,
            lazy: lazyPage(() => import('@/pages/vacancies').then((m) => m.VacancyEditorPage), {
              auth: true,
              roles: ['employer'],
            }),
          },
          {
            path: ROUTES.vacancyEdit,
            lazy: lazyPage(() => import('@/pages/vacancies').then((m) => m.VacancyEditorPage), {
              auth: true,
              roles: ['employer'],
            }),
          },
          {
            path: ROUTES.company,
            lazy: lazyPage(() => import('@/pages/company').then((m) => m.CompanyPage)),
          },
          {
            path: ROUTES.candidate,
            lazy: lazyPage(() => import('@/pages/candidate').then((m) => m.CandidatePage)),
          },
          {
            path: ROUTES.profile,
            lazy: lazyPage(
              () => import('@/pages/profile').then((m) => m.CabinetLayout),
              authRequired,
            ),
            children: [
              {
                index: true,
                lazy: lazyPage(() => import('@/pages/profile').then((m) => m.CabinetHomePage)),
              },
              {
                path: 'invitations',
                lazy: lazyPage(() => import('@/pages/profile').then((m) => m.InvitationsPage)),
              },
              {
                path: 'resume',
                lazy: lazyPage(() => import('@/pages/profile').then((m) => m.ResumePage)),
              },
              {
                path: 'category',
                lazy: lazyPage(() => import('@/pages/profile').then((m) => m.CategoryPage)),
              },
              {
                path: 'settings',
                lazy: lazyPage(() => import('@/pages/profile').then((m) => m.SettingsPage)),
              },
              {
                path: 'company',
                lazy: lazyPage(() => import('@/pages/profile').then((m) => m.CompanyProfilePage)),
              },
            ],
          },
          {
            path: ROUTES.fspCallback,
            lazy: lazyPage(() => import('@/pages/fsp-callback').then((m) => m.FspCallbackPage), {
              auth: true,
              roles: ['candidate'],
            }),
          },
          {
            path: ROUTES.calendar,
            lazy: lazyPage(
              () => import('@/pages/calendar').then((m) => m.CalendarPage),
              authRequired,
            ),
          },
          {
            path: ROUTES.feed,
            lazy: lazyPage(() => import('@/pages/feed').then((m) => m.FeedPage), {
              auth: true,
              roles: ['candidate', 'employer'],
            }),
          },
          {
            path: ROUTES.feedSwipe,
            lazy: lazyPage(() => import('@/pages/feed').then((m) => m.FeedSwipePage), {
              auth: true,
              roles: ['candidate', 'employer'],
            }),
          },
          {
            path: ROUTES.responses,
            lazy: lazyPage(() => import('@/pages/responses').then((m) => m.ResponsesPage), {
              auth: true,
              roles: ['candidate', 'employer'],
            }),
          },
          {
            // Legacy entry point of the employer's swipe deck.
            path: ROUTES.matching,
            lazy: lazyPage(() => import('@/pages/feed').then((m) => m.FeedSwipePage), {
              auth: true,
              roles: ['employer'],
            }),
          },
          {
            path: ROUTES.matchingProfile,
            lazy: lazyPage(
              () => import('@/pages/matching').then((m) => m.MatchingProfilePage),
              authRequired,
            ),
          },
          {
            path: ROUTES.testing,
            lazy: lazyPage(() => import('@/pages/testing').then((m) => m.TestingPage), {
              auth: true,
              roles: ['candidate', 'employer'],
            }),
          },
          {
            path: ROUTES.testBuilder,
            lazy: lazyPage(() => import('@/pages/test-builder').then((m) => m.TestBuilderPage), {
              auth: true,
              roles: ['employer'],
            }),
          },
          {
            path: ROUTES.admin,
            lazy: lazyPage(() => import('@/pages/admin').then((m) => m.AdminPage), {
              auth: true,
              roles: ['admin'],
            }),
          },
          {
            path: '*',
            lazy: lazyPage(() => import('@/pages/not-found').then((m) => m.NotFoundPage)),
          },
        ],
      },
    ],
  },
]
