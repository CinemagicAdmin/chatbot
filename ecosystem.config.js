module.exports = {
  apps: [
    {
      name: "vendit-chatbot",
      script: "main.py",
      interpreter: "python",
      cwd: __dirname,
      env: {
        PORT: 8082,
      },
      watch: false,
      autorestart: true,
      max_restarts: 10,
    },
  ],
};
