mod commands;
mod rpc;

use rpc::FreeBankClient;
use std::sync::Arc;
use tokio::sync::Mutex;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(Arc::new(Mutex::new(FreeBankClient::default())))
        .invoke_handler(tauri::generate_handler![
            commands::get_balance,
            commands::get_new_address,
            commands::send_transaction,
            commands::get_transactions,
            commands::connect_node,
            commands::get_connection_status,
            commands::get_blockchain_info,
            commands::rpc_call,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
