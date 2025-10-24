from src.web_app import create_app
import threading
import webbrowser


def main():
    def _open():
        try:
            webbrowser.open('http://127.0.0.1:5000')
        except Exception:
            pass
    threading.Timer(1.0, _open).start()
    create_app().run(host='127.0.0.1', port=5000, debug=True)


if __name__ == '__main__':
    main()


