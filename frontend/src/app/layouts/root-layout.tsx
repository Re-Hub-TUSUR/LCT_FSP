import { Outlet, useNavigation } from 'react-router'
import { Loader } from '@/shared/ui'

/** Every page is a lazy chunk: while the next one loads, the current screen stays and is dimmed. */
export function RootLayout() {
  const navigation = useNavigation()

  return (
    <>
      {navigation.state === 'loading' && (
        <div className="route-loader">
          <Loader />
        </div>
      )}
      <Outlet />
    </>
  )
}
