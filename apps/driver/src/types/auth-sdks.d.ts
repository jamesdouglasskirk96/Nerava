// Type declarations for third-party auth SDK globals

interface GoogleAccountsId {
  initialize(config: {
    client_id: string
    callback: (response: { credential: string; select_by: string }) => void
    auto_select?: boolean
    cancel_on_tap_outside?: boolean
  }): void
  prompt(notification?: (status: { isNotDisplayed: () => boolean; isSkippedMoment: () => boolean }) => void): void
  renderButton(
    parent: HTMLElement,
    options: {
      type?: 'standard' | 'icon'
      theme?: 'outline' | 'filled_blue' | 'filled_black'
      size?: 'large' | 'medium' | 'small'
      text?: string
      shape?: string
      width?: number
    },
  ): void
  disableAutoSelect(): void
}

declare namespace google {
  namespace accounts {
    const id: GoogleAccountsId
  }
}

declare namespace AppleID {
  namespace auth {
    function init(config: {
      clientId: string
      scope: string
      redirectURI: string
      usePopup: boolean
    }): void
    function signIn(): Promise<{
      authorization: {
        id_token: string
        code?: string
        state?: string
      }
      user?: {
        name?: { firstName?: string; lastName?: string }
        email?: string
      }
    }>
  }
}
