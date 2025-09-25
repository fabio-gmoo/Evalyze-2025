import { Component } from '@angular/core';
import { Navbar } from '@/components/navbar/navbar';
import { Hero } from '@/components/hero/hero';
import { Features } from '@/components/features/features';
import { Benefits } from '@/components/benefits/benefits';
import { Testimonials } from '@/components/testimonials/testimonials';
import { Cta } from '@/components/cta/cta';
import { Footer } from '@/components/footer/footer';

@Component({
  selector: 'app-home',
  imports: [Navbar, Hero, Features, Benefits, Testimonials, Cta, Footer],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {}
