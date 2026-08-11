FROM apify/actor-python-playwright-camoufox:3.12-1.58.0

# Do NOT set WORKDIR: the base image sets WORKDIR /usr/src/app and a *relative*
# ENTRYPOINT (./xvfb-entrypoint.sh, which starts Xvfb for the headed browser).
# Overriding WORKDIR would make that relative entrypoint unresolvable and the
# container would fail to start. COPY into the inherited workdir instead.
COPY . ./

# playwright + camoufox (and the pre-fetched browser) come from the base image.
# requirements.txt must NOT reinstall them, or the browser version will mismatch.
RUN pip install -r requirements.txt

# One container == one account. Mount state + select the account file at run time.
# Paths are under the base image's workdir (/usr/src/app); verify with:
#   docker run --rm --entrypoint pwd neopets-playwright-helper-x86:latest
#
#   docker run --rm \
#     -v "$PWD/accounts:/usr/src/app/accounts:ro" \
#     -v "$PWD/sessions:/usr/src/app/sessions" \
#     -v "$PWD/time:/usr/src/app/time" \
#     -e ACCOUNT_FILE=/usr/src/app/accounts/account_0.json \
#     neopets-playwright-helper-x86:latest
CMD ["python", "main.py"]