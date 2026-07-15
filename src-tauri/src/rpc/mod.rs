//! JSON-RPC client for freebankd (FreeBank drivechain, slot 130)

use base64::{engine::general_purpose::STANDARD, Engine};
use serde_json::{json, Value};

/// FreeBank JSON-RPC client
pub struct FreeBankClient {
    url: Option<String>,
    auth: Option<String>,
    client: reqwest::Client,
}

impl Default for FreeBankClient {
    fn default() -> Self {
        Self {
            url: None,
            auth: None,
            client: reqwest::Client::new(),
        }
    }
}

impl FreeBankClient {
    /// Configure the RPC connection
    pub fn configure(&mut self, url: &str, user: &str, password: &str) {
        self.url = Some(url.to_string());
        self.auth = Some(STANDARD.encode(format!("{}:{}", user, password)));
    }

    /// Check if client is configured
    pub fn is_configured(&self) -> bool {
        self.url.is_some() && self.auth.is_some()
    }

    /// Make a JSON-RPC call
    pub async fn call(&self, method: &str, params: Vec<Value>) -> Result<Value, String> {
        let url = self.url.as_ref().ok_or("RPC not configured")?;
        let auth = self.auth.as_ref().ok_or("RPC not configured")?;

        let body = json!({
            "jsonrpc": "1.0",
            "id": "freebank-wallet",
            "method": method,
            "params": params
        });

        let response = self
            .client
            .post(url)
            .header("Authorization", format!("Basic {}", auth))
            .header("Content-Type", "application/json")
            .json(&body)
            .send()
            .await
            .map_err(|e| format!("Request failed: {}", e))?;

        if !response.status().is_success() {
            return Err(format!("HTTP error: {}", response.status()));
        }

        let result: Value = response
            .json()
            .await
            .map_err(|e| format!("JSON parse error: {}", e))?;

        // Check for RPC error
        if let Some(error) = result.get("error") {
            if !error.is_null() {
                let msg = error["message"].as_str().unwrap_or("Unknown RPC error");
                return Err(format!("RPC error: {}", msg));
            }
        }

        Ok(result["result"].clone())
    }
}
