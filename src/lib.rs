use zed::{LanguageServerId, Result};
use zed_extension_api::{self as zed, Command};

struct CommonLispExtension;

impl zed::Extension for CommonLispExtension {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        language_server_id: &LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<Command> {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/home/sam".to_string());

        Ok(Command {
            command: "/usr/bin/python3".to_string(), // Use full path
            args: vec![format!("{}/.local/bin/commonlisp-bridge.py", home)],
            env: Default::default(),
        })
    }
}

zed::register_extension!(CommonLispExtension);
