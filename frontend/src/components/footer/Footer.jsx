import React from "react";
import { Layout, Typography } from "antd";

const { Footer } = Layout;

const AppFooter = () => {
  return (
    <Footer style={{ backgroundColor: "#f0f2f5", textAlign: "center", padding: "24px 0" }}>
      <Typography.Text style={{ color: "#7A7A7E", fontSize: "14px", fontWeight: 300 }}>
        ©2025 CosmoChain. All rights reserved.
      </Typography.Text>
    </Footer>
  );
};

export default AppFooter;