import { createBrowserRouter } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Campaigns } from "./pages/Campaigns";
import { CreateCampaign } from "./pages/CreateCampaign";
import { CampaignDetail } from "./pages/CampaignDetail";
import { ChargerExplorer } from "./pages/ChargerExplorer";
import { Billing } from "./pages/Billing";
import { Settings } from "./pages/Settings";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "campaigns", Component: Campaigns },
      { path: "campaigns/create", Component: CreateCampaign },
      { path: "campaigns/:id", Component: CampaignDetail },
      { path: "charger-explorer", Component: ChargerExplorer },
      { path: "billing", Component: Billing },
      { path: "settings", Component: Settings },
    ],
  },
]);
