import { Layout } from 'antd';

const { Footer } = Layout;

export default function AppFooter() {
  return (
    <Footer style={{ textAlign: 'center', backgroundColor: '#f0f2f5' }}>
      ©2025 CosmoChain. All rights reserved.
    </Footer>
  );
}