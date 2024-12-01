import { create } from "zustand";

interface userData {
  id: string;
  email: string;
  name: string;
  idToken: string;
  groups: string;
  accessToken: string;
}

interface UserInterface {
  userData: userData | null;
  setUserData: (newValue: userData | null) => void;
}

const useUserStore = create<UserInterface>((set) => ({
  userData: null,
  setUserData: (newUser: userData | null) => set({ userData: newUser }),
}));

export { useUserStore };
