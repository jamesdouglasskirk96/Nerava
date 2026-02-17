import Foundation

final class BackgroundTimer {
    private var timer: DispatchSourceTimer?
    private let deadline: Date
    private let handler: () -> Void

    init(deadline: Date, handler: @escaping () -> Void) {
        self.deadline = deadline
        self.handler = handler

        let interval = deadline.timeIntervalSinceNow
        guard interval > 0 else {
            DispatchQueue.main.async { handler() }
            return
        }

        timer = DispatchSource.makeTimerSource(queue: .main)
        timer?.schedule(deadline: .now() + interval)
        timer?.setEventHandler { [weak self] in
            self?.handler()
        }
        timer?.resume()
    }

    func cancel() {
        timer?.cancel()
        timer = nil
    }

    deinit {
        cancel()
    }
}
