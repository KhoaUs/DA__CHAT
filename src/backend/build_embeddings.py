import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. Load data
df = pd.read_csv(r"data\data_fixed.csv")

# 2. Chọn model embedding
# all-MiniLM-L6-v2: nhanh, 384 chiều, đủ tốt cho sản phẩm
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 3. Chuẩn hoá text (có thể reuse _normalize_text của bạn)
def preprocess_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return name.strip()

names = df["product_name"].astype(str).map(preprocess_name).tolist()

# 4. Encode theo batch để tránh hết RAM
embeddings = model.encode(
    names,
    batch_size=64,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True,  # rất tiện cho cosine similarity
)

print("Embeddings shape:", embeddings.shape)  # (N, D)

# 5. Lưu embedding ra file riêng (POC)
np.save(r"data\product_name_embeddings.npy", embeddings)

# 6. Nếu muốn lưu kèm vào dataframe để export parquet
df_emb = df.copy()
# không nhét nguyên vector vào CSV (rất xấu), nên dùng parquet
df_emb["product_embedding"] = list(embeddings)

df_emb.to_parquet("data_final_with_emb.parquet", index=False)
