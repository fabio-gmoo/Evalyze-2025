import { Component, inject, OnInit, HostListener } from '@angular/core';
import { ViewMode } from '@interfaces/vacante-model';
import { CommonModule } from '@angular/common';
import { Auth } from '@services/auth';
import { Me } from '@interfaces/token-types-dto';
import { Observable } from 'rxjs';
import { Router } from '@angular/router';

@Component({
  selector: 'app-vacancy-header',
  imports: [CommonModule],
  templateUrl: './vacancy-header.html',
  styleUrl: './vacancy-header.scss',
})
export class VacancyHeader implements OnInit {
  private auth = inject(Auth);
  private router = inject(Router);

  user$: Observable<Me | null> = this.auth.me$;
  user: Me | null = null;
  isDropdownOpen = false;

  ngOnInit() {
    this.user$.subscribe((me) => {
      this.user = me;
    });
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.user-info')) {
      this.isDropdownOpen = false;
    }
  }

  toggleDropdown() {
    this.isDropdownOpen = !this.isDropdownOpen;
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  get viewMode() {
    return this.user?.role === 'company' ? 'company' : 'candidate';
  }

  get userName(): string {
    if (!this.user) return 'Usuario';
    return this.user.full_name || this.user.email;
  }

  get userInitials(): string {
    if (!this.user) return 'U';

    if (this.user.full_name) {
      const names = this.user.full_name.trim().split(' ');
      if (names.length >= 2) {
        return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
      }
      return this.user.full_name.substring(0, 2).toUpperCase();
    }

    return this.user.email.substring(0, 2).toUpperCase();
  }
}
