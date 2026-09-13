import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

load_dotenv()

w = WorkspaceClient(
    host=os.environ["DATABRICKS_HOST"],
    token=os.environ["DATABRICKS_TOKEN"],
)

VOLUME_ROOT = "/Volumes/equinor_asa_volve_data_village/public/volve"
REMOTE_FOLDERS = ["Production_data", "Reports", "Well_technical_data"]
LOCAL_ROOT = os.path.join("data", "raw")


def download_dir(remote_path, local_path):
    os.makedirs(local_path, exist_ok=True)
    for entry in w.files.list_directory_contents(remote_path):
        remote_item = f"{remote_path}/{entry.name}"
        local_item = os.path.join(local_path, entry.name)

        if entry.is_directory:
            download_dir(remote_item, local_item)
            continue

        remote_size = getattr(entry, "file_size", None)
        if os.path.exists(local_item):
            local_size = os.path.getsize(local_item)
            if remote_size is not None and local_size == remote_size:
                print(f"Skipping (already have it): {remote_item}")
                continue
            print(f"Re-downloading (size mismatch): {remote_item}")

        resp = w.files.download(remote_item)
        tmp_path = local_item + ".part"
        with open(tmp_path, "wb") as f:
            f.write(resp.contents.read())
        os.replace(tmp_path, local_item)  # atomic rename — only "completes" if fully written
        print(f"Downloaded: {remote_item}")


if __name__ == "__main__":
    for folder in REMOTE_FOLDERS:
        remote = f"{VOLUME_ROOT}/{folder}"
        local = os.path.join(LOCAL_ROOT, folder)
        print(f"--- {folder} ---")
        download_dir(remote, local)
    print("Done.")