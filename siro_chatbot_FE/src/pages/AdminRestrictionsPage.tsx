import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2, ShieldCheck, SlidersHorizontal } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "@/App";


interface ChatbotCategory {
  category_key: string;
  category_name: string;
  description: string;
  is_enabled: boolean;
  updated_at: string;
}

const AdminRestrictionsPage = () => {
  const navigate = useNavigate();

  const [categories, setCategories] = useState<ChatbotCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getAdminHeaders = () => {
    const token = localStorage.getItem("admin_token");
    return {
      Authorization: `Bearer ${token}`,
    };
  };

  const fetchCategories = async () => {
    setError(null);
    setLoading(true);

    try {
      const res = await axios.get(`${API_BASE_URL}/admin/categories`, {
        headers: getAdminHeaders(),
      });

      setCategories(res.data.categories || []);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Kategoriler alınamadı.");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleCategory = async (categoryKey: string, nextValue: boolean) => {
    const previousCategories = categories;

    setCategories((prev) =>
      prev.map((cat) =>
        cat.category_key === categoryKey
          ? { ...cat, is_enabled: nextValue }
          : cat
      )
    );

    setSavingKey(categoryKey);
    setError(null);

    try {
      await axios.put(
        `${API_BASE_URL}/admin/categories`,
        {
          category_key: categoryKey,
          is_enabled: nextValue,
        },
        {
          headers: getAdminHeaders(),
        }
      );
    } catch (err: any) {
      setCategories(previousCategories);
      setError(err?.response?.data?.detail || "Kategori güncellenemedi.");
    } finally {
      setSavingKey(null);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(249,115,22,0.13),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_24%),linear-gradient(to_bottom_right,#fff7ed,#f8fbff,#eef7f3)]">
      <header className="sticky top-0 z-30 border-b border-white/40 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-0 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/admin")}
              className="flex h-11 w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:bg-slate-50"
              title="Admin panele dön"
            >
              <ArrowLeft size={20} />
            </button>

            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-emerald-500 text-white shadow-lg shadow-orange-200">
              <ShieldCheck size={24} />
            </div>

            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-800">
                Sınırlandırmalar
              </h1>
              <p className="text-sm text-slate-500">
                Chatbot’un cevaplayabileceği kategorileri yönetin
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <section className="mb-8 overflow-hidden rounded-[28px] border border-white/50 bg-white/70 p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur-xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-orange-50 px-4 py-1.5 text-sm font-medium text-orange-700">
            <SlidersHorizontal size={16} />
            Kategori Sınırlandırma 
          </div>

          <h2 className="text-3xl font-bold tracking-tight text-slate-800">
            Cevap verilebilecek konuları seçin
          </h2>

          <p className="mt-3 w-full text-base leading-7 text-slate-600">
            Sirobot'un cevaplayabileceği kategorileri yönetin. Aktif olmayan kategorilerdeki sorular chatbot tarafından cevaplanmaz.
          </p>
        </section>

        {error && (
          <div className="mb-5 rounded-2xl border border-red-100 bg-red-50/80 px-5 py-4 text-sm font-medium text-red-600 shadow-sm backdrop-blur">
            {error}
          </div>
        )}

        <section className="overflow-hidden rounded-[28px] border border-white/50 bg-white/75 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur-xl">
          <div className="border-b border-slate-100/80 px-6 py-5">
            <h3 className="text-xl font-semibold text-slate-800">
              Kategori Listesi
            </h3>
            <p className="mt-1 text-sm text-slate-500">
              Seçili kategoriler chatbot tarafından yanıtlanabilir.
            </p>
          </div>

          <div className="p-6">
            {loading ? (
              <div className="flex items-center gap-3 rounded-2xl bg-slate-50 px-4 py-5 text-slate-500">
                <Loader2 className="animate-spin" size={18} />
                Kategoriler yükleniyor...
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {categories.map((category) => (
                  <label
                    key={category.category_key}
                    className="group flex cursor-pointer items-start gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-orange-200 hover:shadow-md"
                  >
                    <input
                      type="checkbox"
                      checked={Boolean(category.is_enabled)}
                      disabled={savingKey === category.category_key}
                      onChange={(e) =>
                        handleToggleCategory(
                          category.category_key,
                          e.target.checked
                        )
                      }
                      className="mt-1 h-5 w-5 rounded border-slate-300 text-orange-500 focus:ring-orange-500"
                    />

                    <div className="flex-1">
                      <div className="flex items-center justify-between gap-3">
                        <h4 className="text-base font-semibold text-slate-800">
                          {category.category_name}
                        </h4>

                        {savingKey === category.category_key && (
                          <Loader2 className="animate-spin text-slate-400" size={16} />
                        )}
                      </div>

                      <p className="mt-1 text-sm leading-6 text-slate-500">
                        {category.description}
                      </p>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
};

export default AdminRestrictionsPage;