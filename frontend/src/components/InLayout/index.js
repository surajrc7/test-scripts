import React from "react";
import Toolbar from "@mui/material/Toolbar";

import AppHeader from "./AppHeader";
import { Box } from "@mui/system";
import { Outlet } from "react-router-dom";

import LoadingOverlayResource from "src/components/LoadingOverlayResource";

function InLayout() {
    const [mobileOpen, setMobileOpen] = React.useState(false);

    return (
        <Box sx={{ display: "flex" }}>
            <AppHeader mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />

            <LoadingOverlayResource>
                <Box
                    sx={{
                        flexGrow: 1,
                        padding: (theme) => theme.spacing(3),
                    }}
                >
                    <Toolbar />
                    <Box>
                        <Outlet />
                    </Box>
                </Box>
            </LoadingOverlayResource>
        </Box>
    );
}

export default InLayout;
