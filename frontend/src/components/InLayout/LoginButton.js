import LockOpenSharpIcon from '@mui/icons-material/LockOpenSharp';
import { Button } from "@mui/material";

export const LoginButton = () => (
  <Button
    sx={{ border: null }}
    variant="contained"
    startIcon={<LockOpenSharpIcon />}
  >
    Login
  </Button>
);