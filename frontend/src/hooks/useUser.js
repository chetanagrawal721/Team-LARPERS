import { useSyncExternalStore } from "react";
import { getUser, subscribeUser } from "../api";

// The signed-in demo user. Changes made in the top-right menu update every screen.
export function useUser() {
  return useSyncExternalStore(subscribeUser, () => getUser().name);
}
