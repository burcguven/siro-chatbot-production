//AdminPage

import { API_BASE_URL } from "@/App";
import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import {
  LogOut,
  FileText,
  Upload,
  SlidersHorizontal,
  Loader2,
  FolderOpen,
  Trash2,
  ShieldCheck,
  Sparkles,
  CalendarDays,
  HardDriveUpload,
  Files,
  UserPlus,
  X,
  Mail,
  Lock,
} from "lucide-react";


interface UploadedFile {
  filename: string;
  size: number;
  file_type: string;
  last_modified: string;
}

const AdminPage = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [registerModalOpen, setRegisterModalOpen] = useState(false);
  const [newAdminName, setNewAdminName] = useState("");
  const [newAdminEmail, setNewAdminEmail] = useState("");
  const [newAdminPassword, setNewAdminPassword] = useState("");
  const [newAdminPasswordAgain, setNewAdminPasswordAgain] = useState("");
  const [registerLoading, setRegisterLoading] = useState(false);
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [registerSuccess, setRegisterSuccess] = useState<string | null>(null);

  const [uploading, setUploading] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(true);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [filesError, setFilesError] = useState<string | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState<
    "idle" | "uploading" | "processing" | "updating" | "done"
  >("idle");

  const handleLogout = () => {
    localStorage.removeItem("admin_token");
    navigate("/admin-login");
  };

  const handleRegisterAdmin = async (e: React.FormEvent) => {
    e.preventDefault();

    setRegisterError(null);
    setRegisterSuccess(null);

    if (!newAdminName.trim()) {
      setRegisterError("Admin adı zorunludur.");
      return;
    }

    if (!newAdminEmail.trim()) {
      setRegisterError("Admin e-posta adresi zorunludur.");
      return;
    }

    if (newAdminPassword.length < 6) {
      setRegisterError("Şifre en az 6 karakter olmalıdır.");
      return;
    }

    if (newAdminPassword !== newAdminPasswordAgain) {
      setRegisterError("Şifreler eşleşmiyor.");
      return;
    }

    try {
      setRegisterLoading(true);

      const adminToken = localStorage.getItem("admin_token");

      if (!adminToken) {
        navigate("/admin-login");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/admin/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${adminToken}`,
        },
        body: JSON.stringify({
          name: newAdminName,
          email: newAdminEmail,
          password: newAdminPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Admin hesabı oluşturulamadı.");
      }

      setRegisterSuccess("Yeni admin hesabı başarıyla oluşturuldu.");

      setNewAdminName("");
      setNewAdminEmail("");
      setNewAdminPassword("");
      setNewAdminPasswordAgain("");

      setTimeout(() => {
        setRegisterModalOpen(false);
        setRegisterSuccess(null);
      }, 1200);
    } catch (err: any) {
      setRegisterError(err.message || "Admin hesabı oluşturulurken hata oluştu.");
    } finally {
      setRegisterLoading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const fetchFiles = async () => {
    setFilesError(null);
    setLoadingFiles(true);

    try {
      const adminToken = localStorage.getItem("admin_token");

      if (!adminToken) {
        navigate("/admin-login");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/admin/files`, {
        method: "GET",
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${adminToken}`,
          "Cache-Control": "no-cache",
          Pragma: "no-cache",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Dosyalar alınamadı.");
      }

      setFiles(data.files || []);
    } catch (err: any) {
      setFilesError(err.message || "Bir hata oluştu.");
    } finally {
      setLoadingFiles(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleDeleteFile = async (filename: string) => {
    const confirmDelete = window.confirm(
      `${filename} dosyasını silmek istediğinize emin misiniz?`
    );

    if (!confirmDelete) return;

    try {
      const adminToken = localStorage.getItem("admin_token");

      const response = await fetch(
        `${API_BASE_URL}/admin/files/${filename}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${adminToken}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Dosya silinemedi.");
      }

      setFiles((prev) => prev.filter((f) => f.filename !== filename));
      await fetchFiles();
    } catch (err: any) {
      alert(err.message || "Silme sırasında hata oluştu.");
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadMessage(null);
    setUploading(true);
    setUploadProgress(0);
    setUploadStage("uploading");

    try {
      const adminToken = localStorage.getItem("admin_token");

      if (!adminToken) {
        navigate("/admin-login");
        return;
      }

      const formData = new FormData();
      formData.append("file", file);

      await axios.post(
        `${API_BASE_URL}/admin/upload-document`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${adminToken}`,
          },
          onUploadProgress: (progressEvent) => {
            if (!progressEvent.total) return;

            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );

            setUploadProgress(percentCompleted);

            if (percentCompleted >= 100) {
              setUploadStage("processing");
            }
          },
        }
      );

      setUploadProgress(100);
      setUploadStage("processing");

      await new Promise((resolve) => setTimeout(resolve, 100));
      setUploadStage("updating");

      await fetchFiles();

      await new Promise((resolve) => setTimeout(resolve, 100));
      setUploadStage("done");

      setUploadMessage(`Dosya başarıyla yüklendi: ${file.name}`);
    } catch (err: any) {
      const errorMessage =
        err?.response?.data?.detail || err.message || "Bir hata oluştu.";
      setUploadMessage(errorMessage);
      setUploadStage("idle");
      setUploadProgress(0);
    } finally {
      setUploading(false);

      setTimeout(() => {
        setUploadStage("idle");
        setUploadProgress(0);
      }, 1500);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate);
    return date.toLocaleString("tr-TR");
  };

  const getUploadStageText = () => {
    switch (uploadStage) {
      case "uploading":
        return uploadProgress >= 100
          ? "%100 upload tamamlandı"
          : "Dosya yükleniyor...";
      case "processing":
        return "Doküman işleniyor...";
      case "updating":
        return "Bilgi havuzu güncelleniyor...";
      case "done":
        return "Tamamlandı";
      default:
        return "";
    }
  };

  const totalStorage = files.reduce((acc, file) => acc + file.size, 0);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.15),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_24%),linear-gradient(to_bottom_right,#eef4ff,#f8fbff,#eef7f3)]">
      <header className="sticky top-0 z-30 border-b border-white/40 bg-white/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-emerald-500 text-white shadow-lg shadow-blue-200">
              <ShieldCheck size={24} />
            </div>

            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-800">
                Siro Chatbot Admin Panel
              </h1>
              <p className="text-sm text-slate-500">
                Doküman yönetimi ve bilgi havuzu kontrol ekranı
              </p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="group flex items-center gap-2 rounded-xl border border-red-100 bg-white px-4 py-2 text-red-500 shadow-sm transition hover:border-red-200 hover:bg-red-50"
          >
            <LogOut size={18} className="transition group-hover:translate-x-0.5" />
            <span className="font-medium">Çıkış Yap</span>
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          accept=".pdf,.docx,.txt"
        />

        <section className="mb-8 overflow-hidden rounded-[28px] border border-white/50 bg-white/60 p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur-xl">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-2xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700">
                <Sparkles size={16} />
                Admin Workspace
              </div>

              <h2 className="text-3xl font-bold tracking-tight text-slate-800 md:text-4xl">
                Dokümanlarınızı yönetin, bilgi havuzunu güncel tutun
              </h2>

              <p className="mt-3 text-base leading-7 text-slate-600">
                Bu panel üzerinden HR dokümanlarını yükleyebilir, mevcut dosyaları
                görüntüleyebilir ve chatbot’un kullandığı bilgi havuzunu kontrol
                edebilirsiniz.
              </p>
            </div>

            <div className="grid min-w-[280px] grid-cols-2 gap-4">
              <div className="rounded-2xl bg-gradient-to-br from-blue-600 to-blue-500 p-5 text-white shadow-lg shadow-blue-200">
                <div className="mb-3 flex items-center justify-between">
                  <Files size={22} />
                  <span className="text-xs uppercase tracking-[0.2em] text-blue-100">
                    Dosyalar
                  </span>
                </div>
                <div className="text-3xl font-bold">{files.length}</div>
                <div className="mt-1 text-sm text-blue-100">Yüklenen dosya sayısı</div>
              </div>

              <div className="rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 p-5 text-white shadow-lg shadow-emerald-200">
                <div className="mb-3 flex items-center justify-between">
                  <HardDriveUpload size={22} />
                  <span className="text-xs uppercase tracking-[0.2em] text-emerald-100">
                    Depolama
                  </span>
                </div>
                <div className="text-3xl font-bold">
                  {formatFileSize(totalStorage)}
                </div>
                <div className="mt-1 text-sm text-emerald-100">Toplam dosya boyutu</div>
              </div>
            </div>
          </div>
        </section>

        {uploadMessage && (
          <div className="mb-5 rounded-2xl border border-emerald-100 bg-emerald-50/80 px-5 py-4 text-sm font-medium text-emerald-700 shadow-sm backdrop-blur">
            {uploadMessage}
          </div>
        )}

        {filesError && (
          <div className="mb-5 rounded-2xl border border-red-100 bg-red-50/80 px-5 py-4 text-sm font-medium text-red-600 shadow-sm backdrop-blur">
            {filesError}
          </div>
        )}

        <section className="mb-10 grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <button
            onClick={handleUploadClick}
            disabled={uploading}
            className="group relative overflow-hidden rounded-[26px] border border-white/50 bg-white/70 p-6 text-left shadow-[0_15px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_50px_rgba(37,99,235,0.16)] disabled:opacity-60"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/8 to-transparent opacity-0 transition group-hover:opacity-100" />

            <div className="relative">
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 shadow-inner">
                {uploading ? (
                  <Loader2 className="animate-spin" size={28} />
                ) : (
                  <Upload size={28} />
                )}
              </div>

              <h3 className="mb-2 text-xl font-semibold text-slate-800">
                Dosya Yükle
              </h3>

              <p className="text-sm leading-6 text-slate-600">
                HR policy, handbook ve diğer dokümanları sisteme ekleyin.
              </p>

              {(uploading || uploadStage === "done") && (
                <div className="mt-5">
                  <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-500">
                    <span>{getUploadStageText()}</span>
                    <span>
                      {uploadStage === "uploading" || uploadStage === "processing"
                        ? `%${uploadProgress}`
                        : uploadStage === "done"
                        ? "✓"
                        : ""}
                    </span>
                  </div>

                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        uploadStage === "done"
                          ? "bg-gradient-to-r from-emerald-500 to-green-500"
                          : "bg-gradient-to-r from-blue-500 to-emerald-500"
                      }`}
                      style={{
                        width:
                          uploadStage === "processing"
                            ? "100%"
                            : uploadStage === "updating"
                            ? "100%"
                            : uploadStage === "done"
                            ? "100%"
                            : `${uploadProgress}%`,
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </button>
          <button
            onClick={fetchFiles}
            disabled={loadingFiles}
            className="group relative overflow-hidden rounded-[26px] border border-white/50 bg-white/70 p-6 text-left shadow-[0_15px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_50px_rgba(16,185,129,0.16)] disabled:opacity-60"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/8 to-transparent opacity-0 transition group-hover:opacity-100" />
            <div className="relative">
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 shadow-inner">
                {loadingFiles ? (
                  <Loader2 className="animate-spin" size={28} />
                ) : (
                  <FileText size={28} />
                )}
              </div>
              <h3 className="mb-2 text-xl font-semibold text-slate-800">
                Dosyaları Yönet
              </h3>
              <p className="text-sm leading-6 text-slate-600">
                Yüklenmiş dosyaları görüntüleyin, inceleyin ve yönetin.
              </p>
            </div>
          </button>

          <button
            onClick={() => {
              setRegisterModalOpen(true);
              setRegisterError(null);
              setRegisterSuccess(null);
            }}
            className="group relative overflow-hidden rounded-[26px] border border-white/50 bg-white/70 p-6 text-left shadow-[0_15px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_50px_rgba(124,58,237,0.16)]"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-violet-500/8 to-transparent opacity-0 transition group-hover:opacity-100" />

            <div className="relative">
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-50 text-violet-600 shadow-inner">
                <UserPlus size={28} />
              </div>

              <h3 className="mb-2 text-xl font-semibold text-slate-800">
                Yeni Admin Ekle
              </h3>

              <p className="text-sm leading-6 text-slate-600">
                Sisteme yeni admin hesabı tanımlayın.
              </p>
            </div>
          </button>

          <button
            onClick={() => navigate("/admin/restrictions")}
            className="group relative overflow-hidden rounded-[26px] border border-white/50 bg-white/70 p-6 text-left shadow-[0_15px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_20px_50px_rgba(249,115,22,0.16)]"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-orange-500/8 to-transparent opacity-0 transition group-hover:opacity-100" />

            <div className="relative">
              <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-orange-500 shadow-inner">
                <SlidersHorizontal size={28} />
              </div>

              <h3 className="mb-2 text-xl font-semibold text-slate-800">
                Sınırlandırmalar
              </h3>

              <p className="text-sm leading-6 text-slate-600">
                Chatbot’un cevaplayabileceği konu kategorilerini yönetin.
              </p>
            </div>
          </button>
        </section>

        <section className="overflow-hidden rounded-[28px] border border-white/50 bg-white/75 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur-xl">
          <div className="border-b border-slate-100/80 px-6 py-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
                  <FolderOpen size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-slate-800">
                    Yüklenen Dosyalar
                  </h3>
                  <p className="text-sm text-slate-500">
                    Sistemde aktif olarak kullanılan dokümanlar
                  </p>
                </div>
              </div>

              <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-600">
                {files.length} dosya
              </div>
            </div>
          </div>

          <div className="p-6">
            {loadingFiles ? (
              <div className="flex items-center gap-3 rounded-2xl bg-slate-50 px-4 py-5 text-slate-500">
                <Loader2 className="animate-spin" size={18} />
                Dosyalar yükleniyor...
              </div>
            ) : files.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-slate-200 bg-slate-50/70 px-6 py-14 text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-white text-slate-400 shadow-sm">
                  <FolderOpen size={28} />
                </div>
                <h4 className="text-lg font-semibold text-slate-700">
                  Henüz yüklenmiş dosya yok
                </h4>
                <p className="mt-2 max-w-md text-sm leading-6 text-slate-500">
                  İlk dokümanı yüklemek için yukarıdaki “Dosya Yükle” kartını
                  kullanabilirsiniz.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {files.map((file, index) => (
                  <div
                    key={`${file.filename}-${index}`}
                    className="group flex flex-col gap-4 rounded-2xl border border-slate-200/80 bg-white px-5 py-4 shadow-sm transition hover:border-blue-200 hover:shadow-md md:flex-row md:items-center md:justify-between"
                  >
                    <div className="flex items-start gap-4">
                      <div className="mt-1 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                        <FileText size={22} />
                      </div>

                      <div>
                        <div className="text-base font-semibold text-slate-800">
                          {file.filename}
                        </div>
                        <div className="mt-1 text-sm text-slate-500">
                          {file.file_type} • {formatFileSize(file.size)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 md:gap-4">
                      <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-sm text-slate-600">
                        <CalendarDays size={16} />
                        {formatDate(file.last_modified)}
                      </div>

                      <button
                        onClick={() => handleDeleteFile(file.filename)}
                        className="flex h-11 w-11 items-center justify-center rounded-xl bg-red-50 text-red-500 transition hover:bg-red-100 hover:text-red-600"
                        title="Dosyayı sil"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
      {registerModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 px-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-[28px] border border-white/40 bg-white p-7 shadow-[0_25px_80px_rgba(15,23,42,0.25)]">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-violet-600">
                  <UserPlus size={26} />
                </div>

                <h2 className="text-2xl font-bold text-slate-800">
                  Yeni Admin Hesabı
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Yeni admin kullanıcısı oluşturmak için bilgileri girin.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setRegisterModalOpen(false)}
                className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-500 transition hover:bg-slate-200 hover:text-slate-700"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleRegisterAdmin} className="space-y-5">
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Admin Adı
                </label>
                <input
                  type="text"
                  value={newAdminName}
                  onChange={(e) => setNewAdminName(e.target.value)}
                  placeholder="Örn: Yeni Admin"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-800 outline-none transition focus:border-violet-400 focus:bg-white"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Admin E-posta
                </label>
                <div className="relative">
                  <input
                    type="email"
                    value={newAdminEmail}
                    onChange={(e) => setNewAdminEmail(e.target.value)}
                    placeholder="admin@siro.com"
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-11 text-slate-800 outline-none transition focus:border-violet-400 focus:bg-white"
                  />
                  <Mail
                    size={18}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400"
                  />
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Şifre
                </label>
                <div className="relative">
                  <input
                    type="password"
                    value={newAdminPassword}
                    onChange={(e) => setNewAdminPassword(e.target.value)}
                    placeholder="En az 6 karakter"
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-11 text-slate-800 outline-none transition focus:border-violet-400 focus:bg-white"
                  />
                  <Lock
                    size={18}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400"
                  />
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Şifre Tekrar
                </label>
                <div className="relative">
                  <input
                    type="password"
                    value={newAdminPasswordAgain}
                    onChange={(e) => setNewAdminPasswordAgain(e.target.value)}
                    placeholder="Şifreyi tekrar girin"
                    className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 pr-11 text-slate-800 outline-none transition focus:border-violet-400 focus:bg-white"
                  />
                  <Lock
                    size={18}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400"
                  />
                </div>
              </div>

              {registerError && (
                <div className="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-600">
                  {registerError}
                </div>
              )}

              {registerSuccess && (
                <div className="rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
                  {registerSuccess}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setRegisterModalOpen(false)}
                  className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 font-semibold text-slate-600 transition hover:bg-slate-50"
                >
                  Vazgeç
                </button>

                <button
                  type="submit"
                  disabled={registerLoading}
                  className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-violet-600 px-4 py-3 font-semibold text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {registerLoading && <Loader2 className="animate-spin" size={18} />}
                  {registerLoading ? "Oluşturuluyor..." : "Admin Oluştur"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}      
    </div>
  );
};

export default AdminPage;