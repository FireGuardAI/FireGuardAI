function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-2 text-3xl font-bold">FireGuardAI</h1>

        <p className="mb-6 text-gray-600">
          Sign in to your account
        </p>

        <form className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">
              Email
            </label>

            <input
              type="email"
              className="w-full rounded border px-3 py-2"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">
              Password
            </label>

            <input
              type="password"
              className="w-full rounded border px-3 py-2"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded bg-blue-600 px-4 py-2 font-medium text-white"
          >
            Sign In
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage