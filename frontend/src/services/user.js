import { useAuthStore } from "../store/authStore";
import api from "./api";

// Get single user
export const userService = {
  getSingleUser: async ({ id }) => {
    if (!id) return null;
    const token = useAuthStore.getState().token;

    const response = await api.get(`/api/v1/auth/users/${id}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },
}; 

export default userService;
