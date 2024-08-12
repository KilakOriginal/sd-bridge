# sd-bridge
## About this project
sd-bridge is a simple Signal-Discord bridge bot that allows Signal users to
communicate with Discord users and vice versa.

## Setting Up the Project
To get started with this project, follow these steps:

1. **Clone the repository:**
    ```bash
    git clone https://github.com/KilakOriginal/sd-bridge/
    cd sd-bridge
    ```
2. **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```
3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Install [signal-cli](https://github.com/AsamK/signal-cli)**

5. **[Generate a CAPTCHA code](https://signalcaptchas.org/registration/generate)
   and copy the link**

6. **Register your Signal account:**
    ```bash
    signal-cli -u +<COUNTRY_CODE><NUMBER> register --captcha <LINK>
    ```

7. **Remove the config file. The file name is just a number.** By default it is
   located in `~/.local/share/signal-cli/data/<SOME_NUMBER>`. If you used the
   `--config <PATH>` flag with the previous command, then the file you need to
   remove will be located in `<PATH>/<SOME_NUMBER>`.

8. **Link the device:**
    ```bash
    signal-cli link # add --config <PATH> iff you used it in the register command 
    ```

9. **Run the application:**
    ```bash
    python main.py
    ```
