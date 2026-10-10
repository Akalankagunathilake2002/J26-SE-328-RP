# Modern Frontend State Management: Client State vs Server Cache

## Categorizing State in Modern Applications
A common architectural flaw in single-page applications is treating all state as global client state. Modern engineering strictly partitions state into:
1. **Interactive Client State**: Ephemeral UI flags, form wizard inputs, modal toggles, and client themes.
2. **Server State**: Asynchronous, remote data owned by the backend (e.g. user profile, product list, shopping cart) requiring caching, deduplication, and synchronization.

## State Management Libraries
- **React Context**:
  - Built-in dependency injection for passing props down deep component trees without prop drilling.
  - *Pitfall*: Any update to Context forces every consumer component to re-render, causing performance degradation unless aggressively memoized with `useMemo` and `useCallback`.
- **Zustand**:
  - Lightweight, unopinionated client state store using the Pub/Sub pattern outside the React render cycle.
  - Supports atomic state selector hooks (`const token = useAuthStore(s => s.token)`), ensuring components only re-render when their subscribed slice changes.
- **Redux Toolkit (RTK)**:
  - Opinionated framework for complex state machines requiring predictable action dispatching, middleware pipelines (thunks/sagas), and deterministic time-travel debugging.

## Server-State Management with TanStack Query (React Query)
Server state has unique lifecycle challenges: cache invalidation, background refetching on window focus, optimistic UI updates, and request deduplication.
TanStack Query replaces manual `useEffect` fetch loops:
- Automatically caches query keys (`['student', studentId]`).
- Shares pending promises across components to eliminate duplicate HTTP requests.
- Executes **Optimistic Updates**: Mutates local UI state instantly before the server acknowledges the request, automatically rolling back if the network fails.
